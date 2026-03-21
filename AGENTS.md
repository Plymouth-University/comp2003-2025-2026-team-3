# AGENTS.md

## Project purpose
This repository contains a full-stack application with:
- backend in Python under `backend/app`
- frontend in TypeScript under `frontend/src`

## Task focus
When asked to analyze or rewrite documentation:
- prioritize source code in `backend/app` and `frontend/src`
- use existing files in `docs/` as historical context, not guaranteed truth
- treat `node_modules`, `dist`, `__pycache__`, logs, and generated data as non-authoritative unless explicitly requested
- prefer documenting actual implemented behavior over outdated markdown claims

## Documentation goals
Write docs for:
- new human developers
- future AI agents/tools

Docs should explain:
- purpose
- responsibilities
- architecture
- inputs/outputs
- key flows
- dependencies
- failure modes
- setup/run instructions

## Preferred docs structure
- `docs/getting-started/`
- `docs/architecture/`
- `docs/services/`
- `docs/runbooks/`

## Rules
- do not delete legacy docs without first extracting useful information
- flag ambiguities clearly
- separate verified behavior from assumptions
- prefer concise, structured markdown