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

Git blocks branch switching when changes are uncommitted.

Stash allows you to:
- pause current work
- safely move elsewhere
- resume later exactly where you left off

### What does `WIP` mean?

`WIP` = **Work In Progress**

It is simply a label so you remember what the stash contains.

### Save unfinished work
```bash
git stash push -m "WIP"
```

### Restore later
```bash
git stash pop
```

Always run:
```bash
git status
```
after restoring a stash.

---

## 🏷️ Archive a feature branch (NEW STANDARD)

Before deleting any feature branch, we **always create an archive tag**.

This preserves a permanent reference point in project history.

### Why this matters
- preserves long-term development history
- allows lecturers to inspect earlier work
- keeps branch list clean
- prevents accidental loss of context

Tags do **not** move or change — they are permanent bookmarks.

---

### Create an archive tag

While on the feature branch:

```bash
git tag archive/feature-name
git push origin archive/feature-name
```

Example:
```bash
git tag archive/feature-add-latency-logs
git push origin archive/feature-add-latency-logs
```

---

## 🧹 Delete your feature branch after merge

Once the branch is merged and archived:

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

This helps visualise branches and archive tags.
