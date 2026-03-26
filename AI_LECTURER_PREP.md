# AI Lecturer Prep Script

## Purpose

This document is a full study script you can rehearse before discussing the project with an AI lecturer.

It covers:

1. what AI is actually used here
2. what is not AI
3. exact algorithms and formulas used in code
4. why those formulas are reasonable
5. likely viva questions and strong answers

---

## 1. 30-Second Summary Script

Use this first:

> “Our system is a CPU-first hybrid AI service for SecOps tickets.  
> We use a sentence-transformer model (`all-MiniLM-L6-v2`) for semantic category matching, combined with keyword matching for robustness.  
> Priority and assignment are then handled by deterministic formulas and policy rules, not by an LLM.  
> So it is real AI/ML for classification, plus rule-based automation for routing and oversight.”

---

## 2. Strict AI vs Non-AI Classification

### Real AI/ML in this codebase

1. Semantic embedding inference with `SentenceTransformer`
2. Cosine similarity matching between ticket embeddings and category embeddings
3. Hybrid decision path that can use semantic output

### Not AI (deterministic logic)

1. Keyword match counting
2. Priority score formula
3. Assignee recommendation scoring
4. Oversight auto-move and auto-assign guardrails
5. Background loop scheduling

---

## 3. Plain-English Foundation: What Is a Sentence Transformer?

If asked “what is a sentence transformer?” say:

> “It is a neural network model that converts text into a numeric vector (an embedding) so semantic similarity can be measured mathematically. Similar meanings produce vectors that are closer together.”

Important notes:

1. It is based on transformer architecture.
2. We are using it for **embedding generation**, not chat generation.
3. It does not generate free text in our pipeline.
4. It allows CPU inference with smaller models like `all-MiniLM-L6-v2`.

---

## 4. End-to-End Pipeline (What Happens to One Ticket)

1. Extract text fields:
- `title`, `description`, `issue_type`, `sub_issue_type`, `queue`, `source`

2. Normalize/preprocess text:
- lowercase
- regex tokenization
- stop-word removal
- minimum token length filter

3. Compute category signals:
- keyword score per category
- semantic similarity per category (if model is available)

4. Hybrid category choice:
- if keyword confidence is strong (>= threshold), use keyword result
- otherwise use semantic best match
- if semantic model unavailable, fallback to keyword-only / unclassified fallback

5. Compute priority score:
- formula-based score from category weight + urgency terms + semantic confidence + text length

6. Output:
- category
- confidence
- priority label
- priority score
- method used (`keyword`, `semantic`, `keyword_fallback`, etc.)

---

## 5. Exact Algorithms and Formulas From Implementation

## 5.1 Keyword Scoring

For each category:

1. For each configured keyword:
- normalize keyword
- if keyword is a phrase (contains space), check substring in normalized full text
- else check token membership in token set

2. Score contribution per keyword match:
- +1 per match

3. Category keyword score:
- integer count of matched configured keywords

Interpretation:

- This is a bag-of-keywords style symbolic matcher.
- No learned weights here.

## 5.2 Semantic Similarity Scoring

Given:

- ticket embedding vector `v_t`
- category embedding vector `v_c`

Cosine similarity:

`cos(v_t, v_c) = (v_t · v_c) / (||v_t|| * ||v_c||)`

The code scales cosine output from `[-1, 1]` into `[0, 100]`:

`scaled = int(((cos + 1) / 2) * 100)`

Why this works:

1. Cosine gives direction similarity independent of magnitude.
2. Scaling makes scores easier for humans and for downstream formulas.
3. Integer scoring simplifies deterministic post-processing.

## 5.3 Hybrid Category Decision Rule

Let:

- `K_max = max keyword score`
- `K_threshold = MIN_KEYWORD_MATCHES` (currently 2)
- `S_best = category with best semantic score`

Rule:

1. If semantic model unavailable:
- if keywords exist -> `keyword_fallback`
- else -> fallback first configured category as `unclassified`

2. If semantic model available:
- if `K_max >= K_threshold`, choose keyword winner
- else choose `S_best`

Why this rule is useful:

1. Keywords provide precision for explicit known patterns.
2. Semantics provide recall for paraphrased language.
3. Fallback path makes service resilient when model cannot load.

## 5.4 Priority Score Formula

Implemented score:

`priority = clamp( base + urgency + semantic_adj + length_adj, 0, 100 )`

Where:

1. `base = 10 + category_priority_weight`
2. `urgency = 10 * count(urgency_keywords_found_in_text)`
3. `semantic_adj = semantic_scores[predicted_category] // 10`
4. `length_adj = min(word_count // 20, 10)`

Priority labels:

1. `> 80` -> Critical
2. `> 60` -> High
3. `> 40` -> Medium
4. else Low

Why this formula is reasonable:

1. Category weight encodes domain importance.
2. Urgency words capture explicit urgency language.
3. Semantic confidence adds soft evidence.
4. Length term gives mild adjustment for richer incident context.
5. Clamp prevents runaway values.

## 5.5 Assignment Recommendation Score (Not ML)

Candidate profile score is additive deterministic scoring:

1. Specialism match:
- `+100` if profile specialism key equals ticket category key

2. Company continuity:
- primary continuity bonus: `min(60, 20 + 10 * same_company_primary_count)`
- secondary continuity bonus: `min(25, 5 + 5 * same_company_secondary_count)`

3. Current ownership continuity:
- `+30` if already primary
- `+15` if already secondary

4. Workload adjustment:
- Weighted load per profile:
  - primary ticket: `+1.0`
  - primary high/critical extra: `+0.75`
  - secondary ticket: `+0.5`
  - secondary high/critical extra: `+0.25`
- Let `load_delta = profile_load - team_average_load`
- if `load_delta > 0.5`:
  - penalty `= min(45, round(load_delta * 12))`
- if `load_delta < -0.5`:
  - bonus `= min(20, round(abs(load_delta) * 8))`

Why this works operationally:

1. Strongly prioritizes skill match.
2. Preserves customer continuity where possible.
3. Discourages overload concentration.
4. Keeps behavior explainable for audit/review.

## 5.6 Oversight Automation Rules (Not ML)

Queue-wide oversight applies strict policies:

1. If manual override exists:
- do not auto-move

2. If no primary owner:
- auto-assign internally using recommendation/fallback

3. If ticket already started:
- block auto-move

4. If pre-start and recommendation outranks incumbent:
- auto-move internally

5. Otherwise:
- unchanged

This is policy enforcement, not learned behavior.

---

## 6. Important “We Do NOT Use …” Answers

Be precise:

1. We do **not** use K-means, DBSCAN, hierarchical clustering, or topic modeling in production.
2. We do **not** use LLM chat-completion for assignment decisions.
3. We do **not** use reinforcement learning or online learning.
4. We do **not** write assignment back to external Autotask yet.

---

## 7. CPU-Only Design Rationale

If asked “why not full LLM?”:

1. Client constraints: CPU-only, no GPU servers.
2. Need predictable latency and cost.
3. Need deterministic guardrails for operational safety.
4. Need explainability for support and governance.

So chosen design is:

- small embedding model + deterministic routing policy.

---

## 8. Key Weaknesses You Should Acknowledge

1. Assignment/routing does not learn from feedback yet.
2. No external write-back integration yet.
3. No full historical assignment audit timeline yet.
4. No fairness/quality evaluation dashboard yet.

Being explicit about limitations signals strong technical maturity.

---

## 9. 20 Likely Lecturer Questions + Strong Answers

## Q1: Is this really AI?

A: “Yes for semantic classification, no for routing policies. The AI part is sentence-transformer embedding inference and cosine similarity. Assignment automation is deterministic scoring and guardrail logic.”

## Q2: What model do you use and why?

A: “`all-MiniLM-L6-v2` via sentence-transformers. It is lightweight enough for CPU use while providing useful semantic embeddings.”

## Q3: Why cosine similarity?

A: “It compares semantic direction of vectors and is scale-invariant. For embedding retrieval/matching, cosine is standard and computationally efficient.”

## Q4: Is this supervised learning?

A: “The embedding model is pre-trained elsewhere. Our deployment performs inference and category matching against configured category prototypes.”

## Q5: Do you cluster tickets?

A: “No. We do nearest-category similarity scoring, not unsupervised clustering.”

## Q6: How do you handle model unavailability?

A: “Graceful fallback to keyword-only. Service still classifies and does not hard-fail.”

## Q7: Why combine keywords and semantics?

A: “Keywords give precision for known signatures; semantics improve robustness for paraphrases. Hybrid reduces brittleness.”

## Q8: Why is priority not learned?

A: “Operationally we need explainability and predictable behavior under CPU constraints. Formula-based priority is transparent and tunable.”

## Q9: What prevents bad automatic reassignment?

A: “Manual override precedence, started-ticket protection, and only moving pre-start tickets when recommendation score outranks incumbent.”

## Q10: Why call it oversight if it is rules?

A: “Oversight refers to continuous queue monitoring and policy execution, not autonomous reasoning.”

## Q11: How do you avoid overload bias?

A: “Workload-aware penalties/bonuses around team average weighted load reduce concentration on already overloaded analysts.”

## Q12: Is there concept drift handling?

A: “Not formal drift detection yet. Current mitigation is configurable categories and refresh cycles.”

## Q13: Are scores calibrated probabilities?

A: “No. Semantic confidence is a scaled similarity score, not a calibrated probability estimate.”

## Q14: Why integer scaling to 0–100?

A: “Human readability, simple thresholding, and deterministic downstream formulas.”

## Q15: How do you justify assignment fairness?

A: “Current fairness signal is workload balancing only. We explicitly document that advanced fairness analytics are future work.”

## Q16: Any online learning?

A: “No. Behavior changes currently come from config, profile/specialism updates, and deterministic logic.”

## Q17: What is the biggest technical risk now?

A: “Mismatch between internal effective assignment and external system ownership until write-back integration is implemented.”

## Q18: Why not full LLM manager now?

A: “CPU-only constraints plus need for predictable operational safety make deterministic policy + lightweight ML a better near-term fit.”

## Q19: How would you evolve this toward stronger AI?

A: “Add optional LLM advisory explanations first, then evaluation harness, then tightly-guarded LLM-in-the-loop decisions if justified by measured gains.”

## Q20: What proves this is production-minded?

A: “Fallback paths, explicit guardrails, persisted operational state, explainable reasons, and clear separation of ML inference from business policy.”

---

## 10. Rehearsal Script (Long Form, 3–5 minutes)

> “The system is a CPU-optimized hybrid AI service for SecOps ticket operations.  
> On each ticket, we extract relevant text fields, normalize text, compute keyword evidence, and compute semantic similarity using a sentence-transformer embedding model.  
> Category selection follows a hybrid rule: strong keywords can win; otherwise semantic best match wins.  
> Priority is then computed by a deterministic formula from category weight, urgency markers, semantic confidence, and capped length adjustment.  
>  
> For assignment, we deliberately do not use an LLM. We use explainable deterministic scoring: specialism-category match, continuity with same-company tickets, ownership continuity, and workload balancing using weighted active load.  
>  
> Oversight then applies policy guardrails continuously: manual override precedence, block moves on started tickets, and auto-assign when no primary owner exists.  
>  
> So technically, the AI/ML component is the embedding-based semantic classification. The rest is deterministic automation designed for reliability, auditability, and CPU-only deployment constraints.  
>  
> This architecture is intentional for our client environment: low-cost operations, no GPU dependency, predictable behavior, and clear explainability.  
> The next evolution would be external write-back, stronger evaluation metrics, and possibly optional LLM advisory layers with strict safeguards.”

---

## 11. Study Checklist (Use Before Your Meeting)

1. Explain sentence transformer in one minute without jargon.
2. Write cosine similarity and scaling formula from memory.
3. Write priority formula from memory.
4. Explain why no clustering is used.
5. Explain why routing is not ML.
6. Explain CPU-only design tradeoffs clearly.
7. Practice 5 random Q&A prompts from section 9.

If you can do those seven things smoothly, you are in a strong position for detailed AI questioning.
