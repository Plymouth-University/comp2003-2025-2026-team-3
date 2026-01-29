# Merge Conflicts (do not panic)

Merge conflicts are normal.
They do NOT mean you broke the project.
They do NOT mean your work is lost.

This guide explains exactly what to do.

---

## 🧠 What a merge conflict actually means

A merge conflict happens when:

- two people edited the same file
- on the same lines
- on different branches

Git does not know which version is correct,
so it asks a human.

That human is you.

---

## 🚨 What NOT to do

When you see a conflict:

❌ Do not delete files  
❌ Do not start guessing commands  
❌ Do not force push  
❌ Do not panic  

Stop and follow the steps below.

---

## ✅ The correct process

### Step 1 — Update your branch
This is how conflicts usually appear:

```bash
git fetch origin
git switch feature/<your-task>
git merge origin/development
```

If Git reports conflicts, continue.

---

### Step 2 — See which files are conflicted
```bash
git status
```

Git will list files marked as “both modified”.

---

### Step 3 — Open the conflicted file

Inside the file you will see markers like this:

```
<<<<<<< HEAD
your changes
=======
development changes
>>>>>>> origin/development
```

This means:
- top = your version
- bottom = development version

---

### Step 4 — Decide the final correct version

You must:
- choose one side
- or combine both

Then:
- delete the conflict markers
- keep only valid code

The file must compile normally afterwards.

---

### Step 5 — Mark the conflict as resolved
```bash
git add <file>
```

Repeat for every conflicted file.

---

### Step 6 — Finish the merge
```bash
git commit
git push
```

Your branch is now clean and updated.

---

## 🔙 If you want to cancel everything
If you feel stuck:

```bash
git merge --abort
```

This returns your branch to exactly how it was before the merge attempt.

---

## ✅ After resolving conflicts

Once resolved:
- your feature branch includes latest development
- your PR should update automatically
- GitHub will allow merging

---

## 🧘 Final reminder

Conflicts are part of teamwork.
Everyone gets them.
Nothing is broken.
