# Run Entire Codebase

## Purpose

This runbook is now intentionally lightweight.

The detailed startup and onboarding content now lives in `docs/getting-started/` so we do not maintain two competing versions of the same instructions.

Use:

1. [first-time-setup.md](docs/getting-started/first-time-setup.md) for one-time machine and project setup
2. [environment.md](docs/getting-started/environment.md) for backend/frontend configuration values
3. [daily-run.md](docs/getting-started/daily-run.md) for the repeatable day-to-day startup workflow
4. [backend-test-scripts.md](docs/runbooks/backend-test-scripts.md) for fixture expansion, reset, mock provider, and AI-state test workflows
5. [troubleshooting.md](docs/runbooks/troubleshooting.md) if the stack does not boot or behave correctly

## Why This Changed

The repository has three onboarding questions that are similar but not identical:

- how do I set this up the first time?
- what environment values do I need?
- how do I run it every day?

Breaking them up makes the docs easier to maintain and less repetitive than one large “run everything” document.

## Keep This Runbook For

This file should remain the short cross-reference for:

- where the canonical getting-started instructions live
- where to go next when startup fails
