# Updating the `documents` Branch (docs-only workflow)

The `documents` branch exists for documentation only:
- research
- meeting minutes
- presentations
- screenshots
- technical notes
- workflow guides

✅ Allowed: PDFs, MD files, screenshots, minutes, docs  
❌ Not allowed: code folders such as `project-root/` or `SourceCode/`

---

## 1) Basic update workflow (add new docs)

### Step A — Switch to documents and pull latest
```bash
git switch documents
git pull origin documents
```

### Step B — Add your new files
Put new documents inside:
```
Documentation/
  Design/
  Minutes/
  Presentations/
  Research/
  Trello/
  Tech/
  Git/
```

### Step C — Check what changed
```bash
git status
```

### Step D — Commit and push
```bash
git add -A
git commit -m "Docs: <what you added>"
git push origin documents
```

Example:
```bash
git commit -m "Docs: add Sprint 4 meeting minutes"
```

---

## 2) IMPORTANT: keeping `documents` docs-only

Before committing, confirm you did NOT accidentally add code:

```bash
git status
```

If you see folders like:
- `project-root/`
- `SourceCode/` (actual code)
- or any `.py/.ts/.rs` files that are part of the application

---

## 3) Copy a docs folder from another branch into documents (safe sync)

Sometimes work is created on another branch (example: `development`)
and you want to copy ONLY docs into `documents`.

### Example: copy Documentation/Git from a branch into documents
```bash
git switch documents
git pull origin documents

git checkout <other-branch> -- Documentation/Git

git add Documentation/Git
git commit -m "Docs: sync Git guides from <other-branch>"
git push origin documents
```

Replace `<other-branch>` with the real branch name.

---

## 4) If you accidentally brought code into `documents` (fix)

If `git status` shows untracked code folders (example: `project-root/`)
DO NOT commit.

Remove the untracked folder safely:

```bash
git clean -nd
git clean -fd
```

If the folder still exists but is empty, delete it:
```powershell
Remove-Item -Recurse -Force project-root
```

Then confirm:
```bash
git status
```
