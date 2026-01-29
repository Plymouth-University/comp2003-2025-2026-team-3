# Getting Fully Back Up To Date 

This guide is for situations where your local repository is completely out of date.

If you have not pulled for a long time, or things feel broken, follow this exactly.

Do not skip steps.

---

## ⚠️ Important

This guide assumes:
- your code is NOT committed
- your local repo may be weeks behind
- you just want everything up to date safely

If you have important uncommitted work, stop and tell Liam first.

---

## ✅ Step 1 — Save or discard local changes

Check your status:

```bash
git status
```

### If it says:
> “nothing to commit, working tree clean”

You are safe — continue.

---

### If it shows modified files:
You must either **commit** or **stash**.

To temporarily save everything:

```bash
git stash push -m "WIP before update"
```

---

## ✅ Step 2 — Switch to development

```bash
git switch development
```

If Git refuses, run:

```bash
git stash push -m "forced switch"
git switch development
```

---

## ✅ Step 3 — Pull the latest code

```bash
git pull origin development
```

This updates your computer with the latest version of the project.

---

## ✅ Step 4 — Delete old feature branches (important)

Old feature branches cause conflicts.

List your branches:

```bash
git branch
```

Delete any old feature branches:

```bash
git branch -D feature/<old-branch-name>
```

(Only delete feature branches — never delete development or main.)

---

## ✅ Step 5 — Create a fresh feature branch

Never continue work on an old branch.

```bash
git switch -c feature/<new-task-name>
git push -u origin feature/<new-task-name>
```

You are now fully up to date and safe to work.

---

## ✅ Step 6 — Restore stashed work (if needed)

If you stashed earlier:

```bash
git stash pop
```

If conflicts appear, ask Liam.

---

## 🚫 What NOT to do

- Do not keep working on old branches
- Do not push to development
- Do not guess commands
- Do not force push

---

## ✅ Summary (copy/paste)

```bash
git stash push -m "WIP"
git switch development
git pull origin development
git branch -D feature/old-branch
git switch -c feature/new-task
git push -u origin feature/new-task
```
