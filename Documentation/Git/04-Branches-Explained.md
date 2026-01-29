# Branches Explained

This file explains how branches actually work.

---

## 🌳 What is a branch?

A branch is **not a folder**.

A branch is a **timeline of commits**.

Think of Git like this:

- Every commit is a snapshot of the project
- A branch is a pointer that moves forward as you commit

When you create a branch, Git does NOT copy files.
It simply creates a new pointer.

---

## 🔀 What happens when you create a feature branch

When you run:

```bash
git switch -c feature/my-task
```

Git does this:
- creates a new timeline starting from development
- your changes only exist on that branch
- development is completely untouched

This is safe.

---

## 🔁 What happens when you merge a feature branch

When your Pull Request is merged:
- your commits are copied into `development`
- the history is permanently saved
- GitHub records who did what and when

Your work now belongs to the project.

---

## ❌ Why deleting a feature branch does NOT delete work

This is very important:

Deleting a branch does NOT delete commits.

Once merged:
- the commits live in `development`
- the PR remains on GitHub forever
- the author information is preserved

Deleting the feature branch only removes the label.

The work stays.

---

## 💻 Local branches vs GitHub branches

There are two places branches can exist:

### Local branches (your computer)
Example:
```text
feature/my-task
```

### Remote branches (GitHub)
Example:
```text
origin/feature/my-task
```

You can have:
- a local branch without pushing
- a remote branch without having it locally

They are related but separate.

---

## 🔄 Why your computer does NOT auto-update

Git does NOT automatically sync.

If someone merges code:
- GitHub updates
- your laptop does NOT

You must manually pull updates:

```bash
git pull origin development
```

If you do not:
- you work on old code
- your PR will conflict later

---

## ⚠️ Most common mistake

Assuming Git “just updates automatically”.

It does not.

You must pull changes yourself.
