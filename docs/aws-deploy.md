# AWS deploy — Hello Agent (ECR + App Runner)

Two container images (`backend`, `frontend`) are built from this repo, pushed to
**Amazon ECR**, then run as two **AWS App Runner** services.

This document covers **ECR push** (task T031). App Runner service setup is
task T032 (section stub below).

## Prerequisites

- AWS account and IAM principal that can manage ECR
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) v2 configured (`aws configure` or SSO)
- Docker Desktop running locally
- Region of choice (examples use `us-east-1` — replace as needed)

```powershell
$env:AWS_REGION = "us-east-1"
$env:AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
echo "Account=$env:AWS_ACCOUNT_ID Region=$env:AWS_REGION"
```

## 1. Create ECR repositories

One repository per image (recommended):

```powershell
aws ecr create-repository --repository-name hello-agent-backend --region $env:AWS_REGION
aws ecr create-repository --repository-name hello-agent-frontend --region $env:AWS_REGION
```

If a repository already exists, the command returns an error you can ignore, or use:

```powershell
aws ecr describe-repositories --repository-names hello-agent-backend hello-agent-frontend --region $env:AWS_REGION
```

## 2. Authenticate Docker to ECR

```powershell
aws ecr get-login-password --region $env:AWS_REGION `
  | docker login --username AWS --password-stdin "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"
```

## 3. Build images (from repo root)

```powershell
cd C:\Projects\IK\Week_0

docker build -t hello-agent-backend ./backend
docker build -t hello-agent-frontend ./frontend
```

Optional: build for linux/amd64 explicitly (matches App Runner):

```powershell
docker build --platform linux/amd64 -t hello-agent-backend ./backend
docker build --platform linux/amd64 -t hello-agent-frontend ./frontend
```

## 4. Tag for ECR

```powershell
$ECR = "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"
$TAG = "latest"   # or a git sha / version, e.g. git rev-parse --short HEAD

docker tag hello-agent-backend:latest  "$ECR/hello-agent-backend:$TAG"
docker tag hello-agent-frontend:latest "$ECR/hello-agent-frontend:$TAG"
```

## 5. Push both images

```powershell
docker push "$ECR/hello-agent-backend:$TAG"
docker push "$ECR/hello-agent-frontend:$TAG"
```

Verify:

```powershell
aws ecr list-images --repository-name hello-agent-backend --region $env:AWS_REGION
aws ecr list-images --repository-name hello-agent-frontend --region $env:AWS_REGION
```

## Secrets reminder

| Variable | Where | Notes |
|----------|--------|--------|
| `ANTHROPIC_API_KEY` | **Backend** runtime only | Never bake into the image; never put on the frontend |
| `BACKEND_URL` | **Frontend** runtime | Points at the backend public HTTPS URL after App Runner deploy |

## App Runner (T032)

Deploy each ECR image as its own App Runner service:

1. Backend service — set `ANTHROPIC_API_KEY` as a secret/env var; listen on port `8000`.
2. Frontend service — set `BACKEND_URL` to the backend service HTTPS URL; listen on port `8501`.

Detailed App Runner steps will live in this file under T032.
