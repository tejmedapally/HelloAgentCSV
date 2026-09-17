# AWS deploy — Hello Agent (ECR + ECS Express Mode)

Two container images (`backend`, `frontend`) are built from this repo, pushed to
**Amazon ECR**, then run as two **Amazon ECS Express Mode** services.

> **Why not App Runner?** AWS closed App Runner to new customers (2026-04-30) and
> recommends [ECS Express Mode](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html)
> as the replacement. Hello Agent follows that path.

> **Why not `docker compose` on AWS?** Compose is for **local** Docker Desktop
> (`BACKEND_URL=http://backend:8000` only works on Compose’s private network).
> Docker’s Compose→ECS integration is retired. On AWS, deploy the **same images**
> as two Express Mode services (or use the one-shot script in **Part F9**).

This document is a **step-by-step** for:

1. Creating an IAM user (do **not** use the root user day-to-day)
2. Creating an access key + secret
3. Installing and configuring AWS CLI
4. Building and pushing both images to ECR
5. Deploying backend → then frontend in order (Express Mode), including a one-shot script

**ECS Express Mode** deploy is **Part F** below.

Commands assume **Windows PowerShell** and repo root `C:\Projects\IK\Week_0`.
Examples use region `us-east-1` — change if you prefer another region.

If `aws` is not found in PowerShell but CLI is installed:

```powershell
$env:Path = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2;" + $env:Path
```

---

## Part A — Create an IAM user (not root)

**Do not** use the AWS **root** account for ECR/CLI work. Root is for account
recovery only.

1. Sign in to the [AWS Console](https://console.aws.amazon.com/) (root is OK **once** to create the first admin/IAM user).
2. Open **IAM** → **Users** → **Create user**.
3. Username example: `hello-agent-deploy`.
4. (Optional) Enable console access if you want this user to log into the website; for CLI-only you can skip console password.
5. On **permissions**, attach managed policies (fine for Week 0 learning):
   - `AmazonEC2ContainerRegistryFullAccess` — create repos, push/pull images
   - `AmazonECS_FullAccess` — useful later for T032 (ECS Express Mode; optional now)
6. Finish creating the user.

For production later, prefer a tighter custom policy limited to your two repos.

---

## Part B — Create access key and secret

You need an **Access key ID** and a **Secret access key** for the CLI.
These are **not** the same as your IAM username/password.

| Item | Example | Used for |
|------|---------|----------|
| IAM username | `hello-agent-deploy` | Console login (with password) |
| Access key ID | `AKIA...` | CLI (`aws configure` “Access Key ID”) |
| Secret access key | long random string | CLI (`aws configure` “Secret”) |

### Create the key

1. IAM → **Users** → click `hello-agent-deploy`.
2. Open the **Security credentials** tab.
3. Under **Access keys**, click **Create access key**.
4. Choose use case: **Command Line Interface (CLI)** → Next → Create.
5. **Copy both values immediately** (or download the `.csv`):
   - Access key ID
   - Secret access key

### Important

- The **secret is shown only once**. After you leave that page, AWS will **not** show it again.
- If you lost the secret: create a **new** access key, then deactivate/delete the old one.
- Never commit keys to git or put them in this repo. Store them in a password manager.

---

## Part C — Install AWS CLI v2

Official guide: [Installing the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

### Option 1 — MSI (recommended)

1. Download (64-bit Windows):
   - All users (needs admin): https://awscli.amazonaws.com/AWSCLIV2.msi
   - Current user only (no admin): https://awscli.amazonaws.com/AWSCLIV2-User.msi
2. Run the installer → Next → Finish.
3. **Close and reopen** PowerShell.
4. Verify:

```powershell
aws --version
```

You should see `aws-cli/2.x.x ...`.

### Option 2 — winget

```powershell
winget install Amazon.AWSCLI
```

Then open a **new** PowerShell and run `aws --version`.

You can run `aws` from **any** PowerShell. For image build/push steps below, `cd` to the repo root.

---

## Part D — Configure the CLI (`aws configure`)

For this exercise, use an **IAM user access key** (not SSO), unless your school/work already requires SSO.

```powershell
aws configure
```

When prompted, enter:

| Prompt | What to paste |
|--------|----------------|
| AWS Access Key ID | Access key ID (`AKIA...`) — **not** your IAM username |
| AWS Secret Access Key | Secret access key |
| Default region name | e.g. `us-east-1` |
| Default output format | `json` |

This writes credentials under your user profile (typically
`C:\Users\<you>\.aws\credentials` and `.aws\config`) — local only, not in the project.

### Verify identity

```powershell
aws sts get-caller-identity
```

You should see your **account ID** and the IAM user’s **ARN** (not “I’m logged in as root with no user”).

---

## Part E — Push images to ECR

Prerequisites for this part:

- Docker Desktop **running**
- AWS CLI configured (Part D)
- Repo available at `C:\Projects\IK\Week_0`

### E0. Set account and region

```powershell
cd C:\Projects\IK\Week_0

$env:AWS_REGION = "us-east-1"
$env:AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
echo "Account=$env:AWS_ACCOUNT_ID Region=$env:AWS_REGION"
```

### E1. Create ECR repositories

One repository per image:

```powershell
aws ecr create-repository --repository-name hello-agent-backend --region $env:AWS_REGION
aws ecr create-repository --repository-name hello-agent-frontend --region $env:AWS_REGION
```

If a repository already exists, the error is fine — continue. To check:

```powershell
aws ecr describe-repositories --repository-names hello-agent-backend hello-agent-frontend --region $env:AWS_REGION
```

### E2. Authenticate Docker to ECR

```powershell
aws ecr get-login-password --region $env:AWS_REGION `
  | docker login --username AWS --password-stdin "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"
```

You should see `Login Succeeded`.

### E3. Build images (from repo root)

```powershell
cd C:\Projects\IK\Week_0

docker build -t hello-agent-backend ./backend
docker build -t hello-agent-frontend ./frontend
```

Optional — pin platform for ECS / Fargate (linux/amd64):

```powershell
docker build --platform linux/amd64 -t hello-agent-backend ./backend
docker build --platform linux/amd64 -t hello-agent-frontend ./frontend
```

### E4. Tag for ECR

```powershell
$ECR = "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"
$TAG = "latest"   # or a git sha: git rev-parse --short HEAD

docker tag hello-agent-backend:latest  "$ECR/hello-agent-backend:$TAG"
docker tag hello-agent-frontend:latest "$ECR/hello-agent-frontend:$TAG"
```

### E5. Push both images

```powershell
docker push "$ECR/hello-agent-backend:$TAG"
docker push "$ECR/hello-agent-frontend:$TAG"
```

### E6. Verify in ECR

```powershell
aws ecr list-images --repository-name hello-agent-backend --region $env:AWS_REGION
aws ecr list-images --repository-name hello-agent-frontend --region $env:AWS_REGION
```

You can also open **ECR** in the AWS Console and confirm both repositories show the `latest` (or your) tag.

---

## App secrets reminder (runtime — not in the image)

| Variable | Where | Notes |
|----------|--------|--------|
| `ANTHROPIC_API_KEY` | **Backend** only | Never bake into Docker build; never put on the frontend |
| `BACKEND_URL` | **Frontend** only | Backend public HTTPS URL after ECS Express Mode deploy |

---

## Part F — Deploy with ECS Express Mode

Deploy **two** Express Mode services (one image each). Express Mode provisions
Fargate + load balancer + HTTPS URL for you.

### Deploy order (same idea as Compose)

Local Compose starts `backend`, waits until healthy, then starts `frontend` with
`BACKEND_URL=http://backend:8000`. On AWS there is **no** shared Compose DNS
name, so you must:

1. Deploy **backend** (port **8000**, health `/api/v1/health`, `ANTHROPIC_API_KEY`)
2. Wait until `GET {BACKEND_URL}/api/v1/health` returns `{"status":"ok"}`
3. Deploy **frontend** (port **8501**, health `/`, `BACKEND_URL` = backend HTTPS URL)

Do **not** set container port to **80** — targets registered on port 80 will stay
**Unhealthy** because the apps listen on **8000** / **8501**.

Official docs:

- [Console first run](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-first-run.html)
- [CLI first run](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-getting-started.html)
- [Create (full)](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-create-full.html)

### F0. Prerequisites

- Images already in ECR (Parts E0–E6), or use the one-shot script in **F9** which can push
- Default VPC with public subnets in your region (Express Mode uses it by default)
- IAM permissions for ECS Express (e.g. `AmazonECS_FullAccess`) and `iam:PassRole` for the roles below
- Console login as an **IAM user** for day-to-day work (root can create services, but the
  **infrastructure role** still needs the policies in F1 — root is not a substitute for those)

Set the same variables as in Part E:

```powershell
cd C:\Projects\IK\Week_0
$env:Path = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2;" + $env:Path
$env:AWS_REGION = "us-east-1"
$env:AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$ECR = "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"
$TAG = "latest"
```

### F1. IAM roles for Express Mode

Express Mode needs **two** roles (console can create them for you; CLI needs them up front):

| Role | Trusts | Managed policy |
|------|--------|----------------|
| Task execution role (e.g. `ecsTaskExecutionRole`) | `ecs-tasks.amazonaws.com` | `AmazonECSTaskExecutionRolePolicy` |
| Infrastructure role (e.g. `ecsInfrastructureRoleForExpressServices`) | `ecs.amazonaws.com` | `AmazonECSInfrastructureRoleforExpressGatewayServices` |

#### Console (easiest)

When you create the first Express Mode service, choose **Create new role** for
Task execution role and Infrastructure role if the dropdown offers it.

#### CLI (create once per account/region)

```powershell
# Task execution role
aws iam create-role --role-name ecsTaskExecutionRole `
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

aws iam attach-role-policy --role-name ecsTaskExecutionRole `
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Infrastructure role for Express Mode
aws iam create-role --role-name ecsInfrastructureRoleForExpressServices `
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

aws iam attach-role-policy --role-name ecsInfrastructureRoleForExpressServices `
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices
```

#### Required inline policy (ALB / public ingress)

If **Public ingress path** fails with
`AccessDenied ... ecsInfrastructureRoleForExpressServices ... ec2:DescribeAccountAttributes`,
the AWS managed policy alone is not enough. Attach this **inline** policy on
`ecsInfrastructureRoleForExpressServices`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ExpressModeEc2DescribeExtras",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeAccountAttributes",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeInternetGateways"
      ],
      "Resource": "*"
    }
  ]
}
```

IAM Console → Roles → `ecsInfrastructureRoleForExpressServices` → Add permissions →
Create inline policy → paste JSON → name e.g. `ExpressModeEc2DescribeExtras`.

If a role already exists, skip `create-role`. Wait ~1 minute after creating/updating roles
before the first `create-express-gateway-service` call (IAM eventual consistency).

```powershell
$EXEC_ROLE = "arn:aws:iam::${env:AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole"
$INFRA_ROLE = "arn:aws:iam::${env:AWS_ACCOUNT_ID}:role/ecsInfrastructureRoleForExpressServices"
```

### F2. Deploy the **backend** (console)

1. Open [ECS console](https://console.aws.amazon.com/ecs/v2) → **Express mode** → create.
2. **Image**: Browse ECR → `hello-agent-backend` → tag `latest` (or digest).
3. Roles: task execution + infrastructure (create if needed; apply F1 inline policy if ingress failed before).
4. **Additional configurations** (critical):
   - Service name: e.g. `hello-agent-backend`
   - Container port: **`8000`** — **not 80**
   - Health check path: **`/api/v1/health`**
   - Environment variables:
     - Prefer **Secret** type pointing at Secrets Manager for `ANTHROPIC_API_KEY`
     - Or (learning only) plain env `ANTHROPIC_API_KEY` = your real key — never commit it
   - CPU architecture: **X86_64** (matches `linux/amd64` images from this repo)
5. Create → wait until deployment is **ACTIVE** and target group shows **Healthy** on port **8000**.
6. Copy the **Application URL** (form like `https://<name>.ecs.<region>.on.aws`).

That URL is your backend base URL (API at `/api/v1/...`).

Smoke-test:

```powershell
# Replace with your backend Application URL (no trailing slash)
$BACKEND_URL = "https://hello-agent-backend.ecs.us-east-1.on.aws"
curl.exe -s "$BACKEND_URL/api/v1/health"
```

Expect `{"status":"ok"}`. Only then deploy the frontend.

### F3. Deploy the **frontend** (console)

1. ECS → **Express mode** → create again.
2. **Image**: ECR → `hello-agent-frontend` → `latest`.
3. Same roles as backend.
4. **Additional configurations**:
   - Service name: e.g. `hello-agent-frontend`
   - Container port: **`8501`** — **not 80**
   - Health check path: **`/`** (Streamlit)
   - Environment variable:
     - `BACKEND_URL` = the **backend Application URL** from F2 (HTTPS, no trailing slash)
   - Do **not** set `ANTHROPIC_API_KEY` on the frontend
5. Create → wait until **ACTIVE** and targets **Healthy** on port **8501**.
6. Open the frontend Application URL in a browser → upload a CSV from `datasets/` → ask.

### F4. Deploy with AWS CLI (optional, step-by-step)

Use `ConvertTo-Json` so PowerShell quoting stays reliable. Prefer **F9** for one-shot.

#### Backend

```powershell
# Prefer Secrets Manager in real use; plain env is OK for a private learning account.
# Do not commit the real key.
$ANTHROPIC_API_KEY = $env:ANTHROPIC_API_KEY
if (-not $ANTHROPIC_API_KEY) { throw "Set ANTHROPIC_API_KEY first" }

$backendContainer = @{
  image         = "$ECR/hello-agent-backend:$TAG"
  containerPort = 8000
  environment   = @(
    @{ name = "ANTHROPIC_API_KEY"; value = $ANTHROPIC_API_KEY }
    @{ name = "PORT"; value = "8000" }
  )
} | ConvertTo-Json -Compress -Depth 5

aws ecs create-express-gateway-service `
  --region $env:AWS_REGION `
  --service-name hello-agent-backend `
  --execution-role-arn $EXEC_ROLE `
  --infrastructure-role-arn $INFRA_ROLE `
  --primary-container $backendContainer `
  --health-check-path "/api/v1/health" `
  --cpu 1 `
  --memory 2 `
  --cpu-architecture X86_64 `
  --monitor-resources
```

Copy the Application URL / service ARN from the output (or describe later):

```powershell
# aws ecs describe-express-gateway-service --service-arn <BACKEND_SERVICE_ARN> --region $env:AWS_REGION
```

Wait for health before creating the frontend:

```powershell
curl.exe -s "$BACKEND_URL/api/v1/health"   # must return {"status":"ok"}
```

#### Frontend

```powershell
$BACKEND_URL = "https://hello-agent-backend.ecs.us-east-1.on.aws"  # your real URL

$frontendContainer = @{
  image         = "$ECR/hello-agent-frontend:$TAG"
  containerPort = 8501
  environment   = @(
    @{ name = "BACKEND_URL"; value = $BACKEND_URL }
    @{ name = "PORT"; value = "8501" }
  )
} | ConvertTo-Json -Compress -Depth 5

aws ecs create-express-gateway-service `
  --region $env:AWS_REGION `
  --service-name hello-agent-frontend `
  --execution-role-arn $EXEC_ROLE `
  --infrastructure-role-arn $INFRA_ROLE `
  --primary-container $frontendContainer `
  --health-check-path "/" `
  --cpu 1 `
  --memory 2 `
  --cpu-architecture X86_64 `
  --monitor-resources
```

### F5. Update an existing service (new image tag)

```powershell
$updated = @{
  image = "$ECR/hello-agent-backend:$TAG"
} | ConvertTo-Json -Compress

aws ecs update-express-gateway-service `
  --region $env:AWS_REGION `
  --service-arn <SERVICE_ARN> `
  --primary-container $updated `
  --monitor-resources
```

(Adjust image / env as needed for frontend. If you change the backend URL, update
frontend `BACKEND_URL` the same way.)

### F6. Verify the full stack

| Check | Expected |
|-------|----------|
| `GET {BACKEND_URL}/api/v1/health` | `{"status":"ok"}` |
| EC2 → Target groups → registered port | **8000** (backend) / **8501** (frontend), not 80 |
| Open `{FRONTEND_URL}` | Hello Agent UI loads |
| Upload `datasets/ecommerce_faqs.csv` + ask | Grounded answer or clear not-found |
| Frontend task env | Has `BACKEND_URL` only — **no** Anthropic key |

### F7. Cost / cleanup notes

- Express Mode uses **Fargate** (typically **does not scale to zero**) — stop/delete services when idle to avoid ongoing charges.
- Delete Express Mode services from ECS console (Express mode), or via CLI delete APIs when you are done experimenting.
- ECR images incur small storage cost until you delete images/repos.

### F8. Troubleshooting

| Symptom | What to try |
|---------|-------------|
| `AccessDenied` … `ec2:DescribeAccountAttributes` on Public ingress | Attach the F1 inline policy on `ecsInfrastructureRoleForExpressServices`; delete the failed service; recreate |
| Target group **Protocol:Port HTTP:80** + Unhealthy | Container port was set to 80 — recreate with **8000** (backend) or **8501** (frontend) |
| LB targets Unhealthy, tasks Running | Confirm health path (`/api/v1/health` or `/`) and registered **target port** matches the app |
| `Unable to assume` role on create | Wait ~1 min after creating IAM roles; retry |
| Frontend cannot reach backend | `BACKEND_URL` must be the **public HTTPS** backend URL, not `http://backend:8000` |
| Ask fails: API key missing | Key must be on **backend** env/secret only; redeploy backend after setting it |
| Wrong arch | Rebuild/push with `--platform linux/amd64` and use **X86_64** in Express Mode |
| `aws` not recognized | Prepend `$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2` to `PATH` (see top of this doc) |

### F9. One-shot deploy (Compose-like order)

Script: [`scripts/deploy-aws.ps1`](../scripts/deploy-aws.ps1)

It:

1. (Optional) builds/pushes both images to ECR for `linux/amd64`
2. Creates Express Mode **backend** with port **8000** + `ANTHROPIC_API_KEY`
3. Waits until `/api/v1/health` succeeds
4. Creates Express Mode **frontend** with port **8501** + `BACKEND_URL` set to the backend HTTPS URL

```powershell
cd C:\Projects\IK\Week_0
$env:Path = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2;" + $env:Path

# Key from environment or repo-root / backend .env (gitignored)
$env:ANTHROPIC_API_KEY = "sk-ant-your-key"   # or rely on .env

# First time: ensure F1 roles + inline policy exist
.\scripts\deploy-aws.ps1

# Images already in ECR:
.\scripts\deploy-aws.ps1 -SkipPush
```

If a service name already exists, delete it in the ECS Express Mode console (or update
via F5) and re-run. The script is for a clean create in learning accounts.

---

## Related local path

For local parity without AWS: `docker compose up --build` at the repo root
(see root `README.md` and `docker-compose.yml`). Frontend then uses
`BACKEND_URL=http://backend:8000` on the Compose network — that hostname does
**not** exist on Express Mode.
