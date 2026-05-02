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

## 🏷️ After PR is merged (IMPORTANT)

Before deleting any feature branch, we **archive it with a tag**.

### Create archive tag
```bash
git tag archive/feature-name
git push origin archive/feature-name
```

Example:
```bash
git tag archive/feature-add-latency-logs
git push origin archive/feature-add-latency-logs
```

### Then delete the branch
```bash
git switch development
git pull origin development
git branch -d feature/<task>
git push origin --delete feature/<task>
```

Tags remain permanently and preserve history.

---

## 🧠 If confused
```bash
git status
```

If still confused → ask Liam.
