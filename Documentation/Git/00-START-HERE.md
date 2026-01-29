# START HERE (READ THIS BEFORE TOUCHING THE REPO)

If you do not follow this guide, you will cause merge problems for everyone.

This project uses a strict Git workflow.  
Follow it exactly.

---

## 🚦 Important branches in this repository

### development
- Shared team branch
- Protected (you cannot push to it)
- All work must arrive here via Pull Requests

### main
- Final submission branch
- Only updated when we are ready to submit

### documents
- Documentation-only branch
- NO CODE is allowed on this branch

### feature/<task-name>
- Your personal working branch
- Used for ONE task only

Examples:
- feature/add-latency-logs
- feature/fix-ticket-detail
- feature/ui-settings-page

---

## ❗ Golden rules (do not break these)

1. You **must always work on a feature branch**
2. You **must never push to development**
3. You **must open a Pull Request (PR)** to merge work
4. Your branch **must be updated before opening a PR**
5. After merging, your feature branch **must be deleted**

If you are unsure, please ask Liam.

---

## ✅ The only workflow you need

### 1️⃣ Start a new task
```bash
git switch development
git pull origin development
git switch -c feature/<your-task-name>
git push -u origin feature/<your-task-name>
```

---

### 2️⃣ While working
Save your work regularly:

```bash
git add .
git commit -m "Topic: short description"
git push
```

Examples:
- Front-End: fix dashboard layout
- Back-End: add timestamp logging
- Docs: update Git guide

---

### 3️⃣ BEFORE opening a Pull Request (very important)
You must update your branch with development:

```bash
git fetch origin
git merge origin/development
git push
```

This prevents conflicts.

---

### 4️⃣ Open a Pull Request (GitHub website)
- Base branch: `development`
- Compare branch: your `feature/<task-name>`
- Add a short description
- Wait for approval
- Merge using GitHub

⚠️ Do NOT merge locally.

---

### 5️⃣ After your PR is merged
Clean up your branch:

```bash
git switch development
git pull origin development
git branch -d feature/<task-name>
git push origin --delete feature/<task-name>
```

---

### 6️⃣ After someone else merges into development (VERY IMPORTANT)

If another team member merges a feature into `development`,
your local copy is now **out of date**.

Before doing ANY new work, you must run:

```bash
git switch development
git pull origin development
```

This updates your computer with the latest code.

⚠️ If you skip this step:
- you will work on old code
- your future PR will cause conflicts
- GitHub may block your merge

Always pull development **before starting new work**.

---
