# Git Cheat Sheet (minimum you need)

If you forget everything else, use this.

---

## ✅ Start new work
```bash
git switch development
git pull origin development
git switch -c feature/<task>
git push -u origin feature/<task>
```

---

## 💾 Save progress
```bash
git add .
git commit -m "Topic: message"
git push
```

---

## 🔄 Update your branch before PR
```bash
git fetch origin
git merge origin/development
git push
```

---

## 🔀 Open Pull Request (GitHub)
- Base: `development`
- Compare: your feature branch
- Wait for approval
- Merge on GitHub

---

## 🧹 After PR is merged
```bash
git switch development
git pull origin development
git branch -d feature/<task>
git push origin --delete feature/<task>
```

---

## 🧠 If confused
```bash
git status
```

If still confused → ask Liam.
