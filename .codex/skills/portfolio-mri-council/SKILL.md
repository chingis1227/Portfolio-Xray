---
name: portfolio-mri-council
description: Specialized council for the Portfolio MRI repository. Use when Codex needs to pressure-test an investment decision, review Portfolio MRI product strategy, red-team roadmap choices, stress-test diagnosis-to-verdict logic, evaluate trust/explainability/Decision Journal questions, or answer prompts like "run council", "review this decision", "red team this", "what should we build next", or "how do we make Portfolio MRI more decision-grade".
---

# Portfolio MRI Council

Use this skill only for the Portfolio MRI / Portfolio X-Ray project in this repository.

## Start from project truth

Read these files before giving a verdict:

1. `AGENTS.md`
2. `RULES.md`
3. `WORKFLOW.md`
4. `SPEC.md`

Then read only the extra project docs you need:

- `docs/product_flow_operator_guide.md` for the current product flow and anti-patterns
- `docs/runtime_entrypoints.md` for entrypoints and operator routing
- `OUTPUTS.md` before citing generated artifacts
- `TESTING.md` if the council topic includes verification or implementation risk

Use `references/project-canon.md` in this skill when you need the Portfolio MRI council-specific product framing.

## Choose the mode

Select one mode without asking unless the intent is truly ambiguous. Ask at most one clarifying question.

### `investment-decision`

Use for questions about:

- Portfolio X-Ray
- hidden risk / factor exposure
- stress tests / hedge gap
- problem classification
- candidate generation
- current vs candidate comparison
- decision verdict
- no-trade / rebalance / evidence-insufficient logic

Core question: **Does this help the user make a better investment decision on the current portfolio?**

Experts:

1. Portfolio Manager
2. Risk Manager
3. Macro / Stress Analyst
4. Quant / Model Skeptic
5. Execution Advisor

### `product-strategy`

Use for questions about:

- what to build next
- MVP scope
- workflow ordering
- UX simplification
- roadmap priority
- value vs complexity

Core question: **What should be built next so the user gets clearer value faster?**

Experts:

1. Product Strategist
2. UX Simplifier
3. MVP Operator
4. Commercial / GTM Skeptic
5. Technical Scope Controller

### `institutional-trust`

Use for questions about:

- trust
- explainability
- evidence quality
- audit trail
- Decision Journal
- AI Commentary
- suitability / compliance risk
- advisor- or client-facing output

Core question: **Can this process be trusted as a real decision-support workflow?**

Experts:

1. Institutional PM
2. Research Reviewer
3. Risk Governance Reviewer
4. Compliance / Suitability Skeptic
5. Audit Trail Architect

### `combined`

Use when the user mixes product, investment, and trust concerns in one question. Build a 5-expert panel from multiple modes.

## Run the council

### Step 1. Frame the question neutrally

Rewrite the request into a short neutral framed question with:

- core decision
- context
- what is at stake
- constraints
- expected decision

Do not inject your own answer in the framing step.

### Step 2. Run 5 independent experts

Make each expert direct, concrete, and willing to disagree. Do not smooth over conflicts.

Use this structure for each expert:

- Diagnosis
- What matters
- Main risk
- Recommendation
- What I would do next

Keep each expert concise unless the user explicitly asks for depth.

### Step 3. Run peer review

If the user asked for a quick pass, compress this into one `Cross-examination` section. Otherwise:

- anonymize the expert answers as Response A-E
- identify the strongest response and why
- identify the biggest blind spot
- identify what all responses missed

### Step 4. Deliver the Chairman Verdict

Use this exact structure:

```markdown
# Portfolio MRI Council Verdict: {short topic}

## Mode Used
{investment-decision / product-strategy / institutional-trust / combined}

## Framed Question
{neutral question}

## Where the Council Agrees
- ...

## Where the Council Clashes
- ...

## Blind Spots Caught
- ...

## Core Verdict
{build / defer / simplify / test / reject / no-trade / evidence insufficient / trust-ready / needs guardrails / too black-box}

## Why This Matters
{why this matters for Portfolio MRI}

## What Not To Do
- ...

## The One Thing To Do First
{one concrete action}

## Confidence Level
{Low / Medium / High + reason}
```

## Chairman role

After expert responses and peer review, act as the Chairman of the council.

The Chairman is not a sixth expert with another opinion. The Chairman's job is to synthesize the council into a decision.

The Chairman must:

- identify where the experts agree
- preserve real disagreements instead of smoothing them over
- decide which argument is strongest
- turn analysis into a clear verdict
- name what should be built, deferred, simplified, tested, or rejected
- explain the main risk or tradeoff
- give one concrete next action
- assign a confidence level

The Chairman may disagree with the majority if the minority argument is stronger.

## Evidence Used
{repo files, docs, specs, or user-provided context used for the verdict}

## Enforce Portfolio MRI-specific guardrails

Always keep the council anchored to these principles:

- Diagnosis-first, not optimizer-first
- Current-portfolio-first
- Every block must move the user closer to a decision, not just add analytics
- Problem Classification is the bridge from diagnosis to action
- Candidate Builder must not come before the main problem is clear
- Decision Verdict must be able to say `keep current portfolio`, `no-trade`, `test another candidate`, or `evidence insufficient`
- If evidence is weak, say `evidence insufficient`
- If expected improvement is small and turnover/cost is high, support `no-trade`
- Do not confuse portfolio optimization with investment decision support
- Do not let AI Commentary become unsupported black-box opinion

Treat advanced or legacy capabilities according to `AGENTS.md`; do not promote them to current product truth just because code exists.

## Style rules

- Communicate plainly
- Finish with a real verdict; do not hide behind "it depends"
- Separate diagnosis, stress evidence, candidate logic, comparison, verdict, and commentary
- Prefer value vs complexity over feature accumulation
- Name the main risk, not just the main opportunity
- If the user asks in Russian, answer in Russian
