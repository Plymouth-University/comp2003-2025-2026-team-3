# Day-to-Day Git Commands

This file contains copy-and-paste commands for normal daily work.

You do NOT need to memorise these.

---

## 🔍 Check where you are

Always check this first if confused.

```bash
git branch --show-current
git status
```

---

## 🔄 Get the latest development branch

Do this every day before starting work.

```bash
git switch development
git pull origin development
```

---

## 🌱 Start a new feature

```bash
git switch development
git pull origin development
git switch -c feature/<task-name>
git push -u origin feature/<task-name>
```

Example:
```bash
git switch -c feature/add-latency-logs
```

---

## 💾 Save your work

Do this regularly.

```bash
git add .
git commit -m "Topic: short description"
git push
```

---

## 🔁 Update your feature branch (IMPORTANT)

Before opening a PR — and often while working:

```bash
git fetch origin
git merge origin/development
git push
```

This reduces merge conflicts.

---

## 🧳 Temporarily save work (stash)

Sometimes Git will not let you switch branches and shows a message like:

> “You have local changes that would be overwritten”

This means:
- you changed files
- but you have NOT committed them yet
- Git is protecting your work from being lost

### What is a stash?

A **stash** is a temporary safe storage area.

Think of it as:
> “Put my unfinished work in a box for a moment.”

Your files are not deleted.
They are just hidden safely by Git.

### Why this exists

You may need to:
- switch branches quickly
- pull urgent updates
- fix something else first

But Git will block you if you have unfinished work.

Stash allows you to:
- pause your current work
- switch branches safely
- return later exactly where you left off

### What does `WIP` mean?

`WIP` = **Work In Progress**

It is just a label so you remember what the stash contains.

### Save your unfinished work
```bash
git stash push -m "WIP"
```

After this:
- your working directory becomes clean
- you can safely switch branches

### Restore your work later
```bash
git stash pop
```

This puts all your changes back exactly as they were.

### Important rules
- Only stash when necessary
- Do NOT forget you stashed something
- Always run `git status` after popping a stash

---

## 🧹 Delete your feature branch after merge

```bash
git switch development
git pull origin development
git branch -d feature/<task-name>
git push origin --delete feature/<task-name>
```

---

## 📜 View commit history as a graph (optional)

```bash
git log --all --decorate --oneline --graph
```

This helps you visualise branches.
