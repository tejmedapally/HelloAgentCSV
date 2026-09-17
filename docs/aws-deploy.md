# AWS deploy — Hello Agent (ECR + App Runner)

Two container images (`backend`, `frontend`) are built from this repo, pushed to
**Amazon ECR**, then run as two **AWS App Runner** services.

This document is a **step-by-step** for:

1. Creating an IAM user (do **not** use the root user day-to-day)
2. Creating an access key + secret
3. Installing and configuring AWS CLI
4. Building and pushing both images to ECR

App Runner service setup is task **T032** (short stub at the end).

Commands assume **Windows PowerShell** and repo root `C:\Projects\IK\Week_0`.
Examples use region `us-east-1` — change if you prefer another region.

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
   - `AWSAppRunnerFullAccess` — useful later for T032 (optional now)
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

Optional — pin platform for App Runner (linux/amd64):

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
| `BACKEND_URL` | **Frontend** only | Backend public HTTPS URL after App Runner deploy |

---

## App Runner (T032)

Deploy each ECR image as its own App Runner service:

1. **Backend** — set `ANTHROPIC_API_KEY` as a secret/env var; port `8000`.
2. **Frontend** — set `BACKEND_URL` to the backend service HTTPS URL; port `8501`.

Detailed App Runner steps will be added under T032.
