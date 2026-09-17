# Deploy Hello Agent to AWS: ECR push (optional) → ECS Express Mode backend → frontend.
# Order mirrors local Compose: backend healthy first, then frontend with BACKEND_URL.
#
# Prerequisites:
#   - AWS CLI v2 on PATH (or under %LOCALAPPDATA%\Programs\Amazon\AWSCLIV2)
#   - Docker Desktop running (if -SkipPush is not set)
#   - IAM roles from docs/aws-deploy.md Part F1
#   - ANTHROPIC_API_KEY, BACKEND_API_KEY, APP_PASSWORD in env or .env (never commit)
#
# Usage (from repo root):
#   $env:BACKEND_API_KEY = "change-me-long-random"
#   $env:APP_PASSWORD = "share-with-graders-only"
#   .\scripts\deploy-aws.ps1
#   .\scripts\deploy-aws.ps1 -SkipPush          # images already in ECR
#   .\scripts\deploy-aws.ps1 -Region us-east-1

[CmdletBinding()]
param(
    [string] $Region = "us-east-1",
    [string] $Tag = "latest",
    [switch] $SkipPush,
    [int] $HealthTimeoutSec = 600
)

$ErrorActionPreference = "Stop"

# Prefer user-local AWS CLI install on Windows if not on PATH
$awsCliDir = Join-Path $env:LOCALAPPDATA "Programs\Amazon\AWSCLIV2"
if ((Test-Path (Join-Path $awsCliDir "aws.exe")) -and ($env:Path -notlike "*$awsCliDir*")) {
    $env:Path = "$awsCliDir;" + $env:Path
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Get-DotEnvValue {
    param([string] $Name, [string] $Path)
    if (-not (Test-Path $Path)) { return $null }
    $line = Get-Content $Path | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -First 1
    if (-not $line) { return $null }
    return ($line -replace "^\s*$Name\s*=\s*", "").Trim().Trim('"').Trim("'")
}

if (-not $env:ANTHROPIC_API_KEY) {
    $fromRoot = Get-DotEnvValue -Name "ANTHROPIC_API_KEY" -Path (Join-Path $RepoRoot ".env")
    $fromBackend = Get-DotEnvValue -Name "ANTHROPIC_API_KEY" -Path (Join-Path $RepoRoot "backend\.env")
    $env:ANTHROPIC_API_KEY = $fromRoot
    if (-not $env:ANTHROPIC_API_KEY) { $env:ANTHROPIC_API_KEY = $fromBackend }
}
if (-not $env:ANTHROPIC_API_KEY) {
    throw "Set ANTHROPIC_API_KEY in the environment or in .env / backend/.env before deploying."
}

foreach ($name in @("BACKEND_API_KEY", "APP_PASSWORD")) {
    if (-not (Get-Item "Env:$name" -ErrorAction SilentlyContinue).Value) {
        $fromRoot = Get-DotEnvValue -Name $name -Path (Join-Path $RepoRoot ".env")
        $fromBackend = Get-DotEnvValue -Name $name -Path (Join-Path $RepoRoot "backend\.env")
        $fromFrontend = Get-DotEnvValue -Name $name -Path (Join-Path $RepoRoot "frontend\.env")
        $val = $fromRoot
        if (-not $val) { $val = $fromBackend }
        if (-not $val) { $val = $fromFrontend }
        if ($val) { Set-Item -Path "Env:$name" -Value $val }
    }
}
if (-not $env:BACKEND_API_KEY) {
    throw "Set BACKEND_API_KEY (same secret on backend + frontend) before deploying."
}
if (-not $env:APP_PASSWORD) {
    throw "Set APP_PASSWORD (Streamlit shared login) before deploying."
}

$env:AWS_REGION = $Region
$AccountId = aws sts get-caller-identity --query Account --output text
if (-not $AccountId) { throw "aws sts get-caller-identity failed. Run aws configure first." }

$Ecr = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$ExecRole = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
$InfraRole = "arn:aws:iam::${AccountId}:role/ecsInfrastructureRoleForExpressServices"

Write-Host "Account=$AccountId Region=$Region Tag=$Tag" -ForegroundColor Cyan

if (-not $SkipPush) {
    Write-Host "`n=== ECR login + build/push ===" -ForegroundColor Cyan
    aws ecr create-repository --repository-name hello-agent-backend --region $Region 2>$null | Out-Null
    aws ecr create-repository --repository-name hello-agent-frontend --region $Region 2>$null | Out-Null

    aws ecr get-login-password --region $Region |
        docker login --username AWS --password-stdin $Ecr

    docker build --platform linux/amd64 -t "hello-agent-backend:$Tag" ./backend
    docker build --platform linux/amd64 -t "hello-agent-frontend:$Tag" ./frontend
    docker tag "hello-agent-backend:$Tag"  "$Ecr/hello-agent-backend:$Tag"
    docker tag "hello-agent-frontend:$Tag" "$Ecr/hello-agent-frontend:$Tag"
    docker push "$Ecr/hello-agent-backend:$Tag"
    docker push "$Ecr/hello-agent-frontend:$Tag"
}

function Get-ExpressEndpoint {
    param([string] $ServiceArn)
    $json = aws ecs describe-express-gateway-service `
        --service-arn $ServiceArn `
        --region $Region `
        --output json | ConvertFrom-Json
    $svc = $json.service
    if (-not $svc) { $svc = $json.expressGatewayService }
    foreach ($prop in @("endpoint", "applicationUrl", "url", "serviceEndpoint")) {
        $val = $svc.$prop
        if ($val) { return $val.TrimEnd("/") }
    }
    # Fallback: search nested properties for an on.aws URL
    $raw = $json | ConvertTo-Json -Depth 20
    if ($raw -match 'https://[a-zA-Z0-9.-]+\.ecs\.[a-z0-9-]+\.on\.aws') {
        return $Matches[0]
    }
    return $null
}

function Wait-BackendHealthy {
    param([string] $BaseUrl, [int] $TimeoutSec)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $health = "$BaseUrl/api/v1/health"
    Write-Host "Waiting for $health ..."
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = curl.exe -sS -m 10 $health
            if ($resp -match '"status"\s*:\s*"ok"') {
                Write-Host "Backend healthy: $resp" -ForegroundColor Green
                return
            }
        } catch { }
        Start-Sleep -Seconds 15
    }
    throw "Timed out waiting for backend health at $health"
}

Write-Host "`n=== Deploy backend (Express Mode) ===" -ForegroundColor Cyan
$backendContainer = @{
    image         = "$Ecr/hello-agent-backend:$Tag"
    containerPort = 8000
    environment   = @(
        @{ name = "ANTHROPIC_API_KEY"; value = $env:ANTHROPIC_API_KEY }
        @{ name = "BACKEND_API_KEY"; value = $env:BACKEND_API_KEY }
        @{ name = "PORT"; value = "8000" }
    )
} | ConvertTo-Json -Compress -Depth 5

$backendOut = aws ecs create-express-gateway-service `
    --region $Region `
    --service-name hello-agent-backend `
    --execution-role-arn $ExecRole `
    --infrastructure-role-arn $InfraRole `
    --primary-container $backendContainer `
    --health-check-path "/api/v1/health" `
    --cpu 1 `
    --memory 2 `
    --cpu-architecture X86_64 `
    --output json 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host $backendOut
    Write-Host @"

If the service already exists, update it instead, or delete it in the ECS console and re-run.
Also confirm IAM roles exist (docs/aws-deploy.md F1) and the infrastructure role has the
DescribeAccountAttributes inline policy if ALB provisioning failed earlier.
"@ -ForegroundColor Yellow
    throw "create-express-gateway-service (backend) failed"
}

$backendJson = $backendOut | ConvertFrom-Json
$backendArn = $backendJson.service.serviceArn
if (-not $backendArn) { $backendArn = $backendJson.expressGatewayService.serviceArn }
Write-Host "Backend service ARN: $backendArn"

$BackendUrl = $null
$deadline = (Get-Date).AddSeconds($HealthTimeoutSec)
while ((Get-Date) -lt $deadline) {
    $BackendUrl = Get-ExpressEndpoint -ServiceArn $backendArn
    if ($BackendUrl) { break }
    Start-Sleep -Seconds 20
}
if (-not $BackendUrl) {
    throw "Could not read backend Application URL from describe-express-gateway-service. Copy it from the ECS console and set frontend BACKEND_URL manually."
}
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Green
Wait-BackendHealthy -BaseUrl $BackendUrl -TimeoutSec $HealthTimeoutSec

Write-Host "`n=== Deploy frontend (Express Mode) ===" -ForegroundColor Cyan
$frontendContainer = @{
    image         = "$Ecr/hello-agent-frontend:$Tag"
    containerPort = 8501
    environment   = @(
        @{ name = "BACKEND_URL"; value = $BackendUrl }
        @{ name = "BACKEND_API_KEY"; value = $env:BACKEND_API_KEY }
        @{ name = "APP_PASSWORD"; value = $env:APP_PASSWORD }
        @{ name = "PORT"; value = "8501" }
    )
} | ConvertTo-Json -Compress -Depth 5

$frontendOut = aws ecs create-express-gateway-service `
    --region $Region `
    --service-name hello-agent-frontend `
    --execution-role-arn $ExecRole `
    --infrastructure-role-arn $InfraRole `
    --primary-container $frontendContainer `
    --health-check-path "/" `
    --cpu 1 `
    --memory 2 `
    --cpu-architecture X86_64 `
    --output json 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host $frontendOut
    throw "create-express-gateway-service (frontend) failed (service may already exist)"
}

$frontendJson = $frontendOut | ConvertFrom-Json
$frontendArn = $frontendJson.service.serviceArn
if (-not $frontendArn) { $frontendArn = $frontendJson.expressGatewayService.serviceArn }

$FrontendUrl = $null
$deadline = (Get-Date).AddSeconds([Math]::Min(300, $HealthTimeoutSec))
while ((Get-Date) -lt $deadline) {
    $FrontendUrl = Get-ExpressEndpoint -ServiceArn $frontendArn
    if ($FrontendUrl) { break }
    Start-Sleep -Seconds 20
}

Write-Host "`n=== Deploy submitted ===" -ForegroundColor Green
Write-Host "Backend:  $BackendUrl"
Write-Host "Frontend: $(if ($FrontendUrl) { $FrontendUrl } else { '(check ECS console Application URL)' })"
Write-Host "Open the frontend URL → enter APP_PASSWORD → upload datasets/*.csv → ask."
