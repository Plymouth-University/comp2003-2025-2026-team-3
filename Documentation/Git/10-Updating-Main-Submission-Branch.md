# Updating `main` (Final Submission Branch)

`main` is the submission branch. It must contain:
- `project-root/` (code snapshot from `development`)
- `Documentation/` (docs snapshot from `documents`)

We do **not** develop directly on `main`.
We update it intentionally when we want a new “submission snapshot”.

---

## ✅ Normal update process (recommended)

### 1) Make sure your source branches are up to date
```bash
git fetch origin
git switch development
git pull origin development

git switch documents
git pull origin documents
```

### 2) Create an update branch from main
```bash
git switch main
git pull origin main
git switch -c chore/update-main-<date>
```

(Example: `chore/update-main-2026-01-29`)

### 3) Copy the latest folders into the update branch
```bash
git checkout development -- project-root
git checkout documents -- Documentation
```

### 4) Commit and push
```bash
git add -A
git commit -m "Chore: update main with latest code + documentation"
git push -u origin chore/update-main-<date>
```

### 5) Open PR on GitHub
Base: `main`  
Compare: `chore/update-main-<date>`  
Merge after review.

---

## 🧠 What this does (important)
- It updates `main` to match the latest code/docs folders
- It does **not** delete commit history from other branches
- It creates a clear “snapshot” commit for marking

---

## ⚠️ If you see unexpected files on main
Please stop and ask Liam before deleting anything.
We only want: `project-root/`, `Documentation/`, `README.md`.
