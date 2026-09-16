# 3. Git and GitHub — Setup and Day-to-Day Commits

Step-by-step for **Windows PowerShell**. Goal: fix local identity, commit locally, create a GitHub repo, then push changes as you work.

## Prerequisites

- [Git](https://git-scm.com/downloads) installed
- A [GitHub](https://github.com/) account
- Project folder: `C:\Projects\IK\Week_0`

---

## Part A — One-time: set your identity

Git needs your name and email before any commit (fixes `Author identity unknown`).

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Use the email on your GitHub account (or GitHub’s noreply address under Settings → Emails).

Verify:

```powershell
git config --global user.name
git config --global user.email
```

---

## Part B — First local commit (this repo)

If the repo is not initialized yet:

```powershell
cd C:\Projects\IK\Week_0
git init
```

Stage files (review first):

```powershell
git status
git add -A
```

Prefer staging specific paths when possible:

```powershell
git add docs specs .specify .cursor Datasets
```

**Do not** commit secrets (`.env`, API keys) or usually `.venv/`.

Commit with a **simple one-line** message (avoids PowerShell multi-line issues):

```powershell
git commit -m "docs: bootstrap Spec Kit for Hello Agent CSV FAQ"
```

Optional second paragraph:

```powershell
git commit -m "docs: bootstrap Spec Kit for Hello Agent CSV FAQ" -m "Add constitution, feature spec/plan/tasks, and sample datasets."
```

Confirm:

```powershell
git log -1
git status
```

---

## Part C — Create a GitHub repository

1. Open https://github.com/new  
2. Choose a name (e.g. `Week_0` or `hello-agent-csv-faq`)  
3. Leave the repo **empty** (no README, no .gitignore, no license)  
4. Click **Create repository**  
5. Copy the HTTPS URL, e.g. `https://github.com/YOUR_USERNAME/Week_0.git`

---

## Part D — Connect and push the first time

```powershell
cd C:\Projects\IK\Week_0
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Week_0.git
git push -u origin main
```

Replace `YOUR_USERNAME/Week_0` with your real path.

When asked to sign in:

- Browser login, or  
- Personal Access Token as password: https://github.com/settings/tokens (scope: `repo`)

Check remote:

```powershell
git remote -v
```

---

## Part E — Day-to-day: after each task or change

### 1. See what changed

```powershell
git status
git diff
```

### 2. Stage what you want

```powershell
git add path\to\file
# or a folder:
git add backend/
```

### 3. Commit

```powershell
git commit -m "T001: create monorepo directories"
```

Good message style for this project:

- `T001: create monorepo directories`
- `T007: add backend config loader`
- `docs: update quickstart ports`

### 4. Push to GitHub

```powershell
git push
```

---

## Useful commands cheat sheet

| Command | What it does |
|---------|----------------|
| `git status` | What’s changed / staged |
| `git diff` | Unstaged line changes |
| `git diff --staged` | Staged line changes |
| `git add <path>` | Stage specific files |
| `git add -A` | Stage all changes in the repo |
| `git commit -m "msg"` | Save a local snapshot |
| `git push` | Upload commits to GitHub |
| `git pull` | Download others’ commits |
| `git log --oneline -5` | Recent commits |
| `git remote -v` | Show GitHub URL |

---

## Workflow with Spec Kit tasks

1. Implement **one** task (e.g. T001)  
2. Review with `git status` / `git diff`  
3. Mark `- [x]` in `specs/001-csv-faq-agent/tasks.md`  
4. `git add` → `git commit` → `git push`  
5. Next task  

---

## Common errors

| Error | Fix |
|-------|-----|
| `Author identity unknown` | Run Part A (`user.name` / `user.email`) |
| `remote origin already exists` | `git remote set-url origin https://github.com/YOUR_USERNAME/REPO.git` |
| `failed to push` / auth | Sign in again or create a PAT with `repo` scope |
| PowerShell messes up multi-line `-m @"..."@` | Use a single-line `git commit -m "..."` |

---

## Notes

- Setting `user.name` / `user.email` enables **local** commits.  
- **GitHub** gets your code only after `git remote add` + `git push`.  
- GitHub Copilot Pro is unrelated to push access; any GitHub account can host the repo.
