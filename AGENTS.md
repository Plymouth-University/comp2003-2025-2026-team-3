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

## Preferred documentation style
When writing or rewriting documentation, prefer a human-first teaching flow that still stays useful for AI/tools.

Recommended flow inside a document:
- start with the purpose of the system and why it exists
- explain the system in plain English before diving into implementation detail
- describe responsibilities and boundaries with other parts of the codebase
- show how the system works step by step using real code-backed flows
- explain important inputs, outputs, dependencies, configuration, and failure modes
- end with troubleshooting, operational notes, or future-direction notes when useful

Preferred writing style:
- write for developers who may be new to the topic, not just for experts
- explain jargon when first introduced, especially around auth, AI, databases, and infrastructure
- prefer teaching-oriented explanations over dense reference-only notes
- keep docs structured and skimmable, but not so compressed that they stop being educational
- clearly separate verified current behavior from assumptions, recommendations, or future-state ideas

Preferred visuals:
- use Mermaid diagrams whenever they help a developer understand the system faster
- prefer sequence diagrams for request or auth flows
- prefer flowcharts for decision paths, lifecycle steps, and troubleshooting
- prefer ER diagrams for database-backed services and domain models
- only include diagrams that match the current implementation or are clearly labeled as future-state suggestions

Preferred organization:
- avoid duplicating the same setup or architecture explanation in multiple places
- keep one canonical home for a topic, then cross-link from other docs
- if a service benefits from it, it is acceptable to add extra files such as `future-direction.md`, `index.md`, or other focused explainer docs
- optimize for docs that help a teammate understand the system without needing to read much code

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
