# AI Functionality Audit (Strict)

## Purpose

This file answers one question strictly:

**Does this project currently use AI, and if yes, where exactly?**

It also separates AI/ML components from non-AI automation so you can decide whether to keep this approach or add stronger AI.

## Strict Criteria Used In This Audit

I classify something as AI/ML only if it includes at least one of:

1. model-based inference (for example, embeddings or learned model predictions)
2. statistical prediction beyond fixed if/else rules
3. behavior learned from model weights rather than hard-coded business logic

I classify something as **not AI** if it is:

1. deterministic rule logic
2. keyword matching without learned inference
3. workflow automation, scheduling, routing policies, or CRUD/persistence code

## Verdict (Current Code)

### What is genuinely AI/ML

1. **Semantic category scoring with sentence embeddings**
- Uses `sentence-transformers` model `all-MiniLM-L6-v2`.
- Code: `backend/app/services/ai/config.py`, `backend/app/services/ai/categorizer.py`
- This is real ML inference.

2. **Hybrid category decision path when semantic model is available**
- Combines keyword signal with model semantic similarity.
- Code: `backend/app/services/ai/categorizer.py`
- The semantic branch is AI/ML; the keyword branch is not.

### What is AI-assisted but mostly rules

1. **Ticket categorization pipeline overall**
- Includes both model similarity and deterministic keyword/threshold logic.
- Code: `backend/app/services/ai/processor.py`, `categorizer.py`
- So the pipeline is mixed: part AI, part rules.

### What is not AI (important)

1. **Assignment recommendation scoring**
- Specialism match, continuity boost, workload penalties/bonuses, tie-breaking.
- Code: `backend/app/services/ai_assignment_service.py`
- This is deterministic scoring, not ML.

2. **AI oversight auto-assignment / auto-move rules**
- Guardrails like “do not move started tickets”, “assign if no primary”.
- Code: `backend/app/services/ai_oversight_service.py`
- This is workflow automation, not AI.

3. **Background loop / scheduler behavior**
- Periodic refresh + oversight runs.
- Code: `backend/app/main.py`, `backend/app/config.py`
- This is operations automation, not AI.

4. **Manual override behavior**
- Stored state and precedence logic.
- Code: `backend/app/services/ai_state_service.py`, `backend/app/repositories/ai_state_repository.py`
- This is policy/state management, not AI.

5. **No LLM orchestration present**
- No OpenAI/Anthropic/LangChain style LLM runtime calls in backend app logic.
- Current “AI manager” behavior is rules + scoring, not a reasoning LLM agent.

## Practical Interpretation

If your requirement is:

- “Use AI/ML for categorization”: **Yes, currently true** (semantic embeddings).
- “Use a true AI manager brain that reasons and plans”: **No, not currently true**.

Current system is best described as:

**ML-assisted classification + deterministic routing automation**.

## If You Want “More AI” Next

To move from rule automation to stronger AI decisioning, typical next options are:

1. Add an LLM decision layer for assignment reasoning (with hard guardrails).
2. Keep deterministic safety constraints and let LLM propose ranked actions.
3. Add evaluation harnesses to measure LLM/routing quality against known-good outcomes.

Without those additions, this remains a strong rules-first operational system with limited ML components.
