# Git Troubleshooting Guide

If something looks scary, check here first.

Most Git errors are warnings — not disasters.

---

## 😱 “I see a ':' at the bottom and I can’t type”

You are inside Git’s viewer (called `less`).

This happens after commands like:
```bash
git log
git diff
```

### To exit:
Press:
```
q
```

Nothing is broken.

---

## 🔒 “You have uncommitted changes”

Git is protecting your work.

This means:
- you edited files
- but did not commit yet

### Fix options:
Either commit:
```bash
git add .
git commit -m "WIP"
```

Or stash:
```bash
git stash push -m "WIP"
```

---

## 🚫 “Updates were rejected because the remote contains work you do not have”

Your local branch is behind GitHub.

### Fix:
```bash
git pull
```

---

## 🧱 “GitHub will not let me push to development”

This is correct behaviour.

`development` is protected.

You must:
- create a feature branch
- push that
- open a Pull Request

---

## ⚠️ “My Pull Request has conflicts”

This means development moved forward.

### Fix:
```bash
git fetch origin
git merge origin/development
git push
```

If conflicts appear, follow:
`05-Merge-Conflicts.md`