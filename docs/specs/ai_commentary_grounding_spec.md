# AI Commentary Grounding Context Spec

This spec owns the deterministic grounding contract for the target Portfolio MRI
AI Commentary layer.

The implemented artifact is `ai_commentary_context.json`, written by
`src/ai_commentary_context.py` after `decision_verdict.json` is produced in the
candidate comparison / decision-package pipeline.

## Status

Implemented as an additive evidence bundle:

- module: `src/ai_commentary_context.py`
- artifact: `{output_dir_final}/ai_commentary_context.json`
- schema version: `ai_commentary_context_v1`
- tests: `tests/test_ai_commentary_context.py`

This is not a generated natural-language AI commentary. No LLM is called. The
artifact only defines what a later AI Commentary layer may read and how it must
ground claims.

## Product role

Target product architecture includes:

```text
Decision Verdict -> AI Commentary -> Monitoring / What Changed
```

In the current implementation, `ai_commentary_context.json` sits between the
product-facing `decision_verdict.json` and later narrative/commentary surfaces.
It is a safety and grounding layer, not a calculator and not a verdict engine.

## Allowed source artifacts

AI Commentary may use only evidence from allowed deterministic artifacts:

- `portfolio_xray.json`
- `stress_report.json`
- `problem_classification.json`
- `candidate_launchpad.json`
- `candidate_comparison.json`
- `current_vs_candidate.json`
- `selection_decision.json`
- `decision_verdict.json`
- `action_plan.json`
- `monitoring_diff.json`

The current writer always receives downstream decision artifacts available in
the comparison flow. Earlier diagnosis artifacts and monitoring may be absent in
some runs; absent sources must be treated as evidence gaps, not inferred.

## Forbidden claim categories

AI Commentary must not make claims in these categories unless a future canonical
spec explicitly changes this boundary:

- new metric calculation
- unsupported verdict
- trade execution instruction
- schema rename
- data-quality status creation
- performance guarantee
- optimizer formula change
- unstated tax advice

## Required grounding rules

Every future commentary generator that consumes `ai_commentary_context.json`
must obey these rules:

1. Use only values and statuses present in allowed source artifacts.
2. Cite an artifact and field path for every material claim.
3. Do not compute new metrics, thresholds, rankings, or optimizer results.
4. Do not rename or reinterpret Selection Engine statuses.
5. Do not issue trade execution instructions or binding investment advice.
6. State evidence gaps and confidence limitations when source artifacts warn or
   are missing.

## Artifact shape

Top-level fields:

- `schema_version`: `ai_commentary_context_v1`
- `diagnostic_only`: `true`
- `generated_at`: UTC timestamp
- `purpose`: `grounded_ai_commentary_context`
- `allowed_source_artifacts`: list of readable source artifact filenames
- `forbidden_claim_categories`: list of forbidden claim types
- `required_grounding_rules`: list of rules for any future commentary generator
- `commentary_topics`: topic-to-grounding guidance map
- `evidence_references`: material source references with artifact and field path
- `source_artifacts`: presence map for the inputs actually available
- `guardrails`: booleans proving this layer does not call an LLM, calculate
  metrics, alter selection/verdict, or execute trades
- `warnings`: missing-source and upstream-warning list

## Evidence references

Each `evidence_references` row contains:

- `artifact`: source artifact filename
- `field_path`: field path inside the artifact
- optional `value`: source value or compact excerpt
- optional `summary`: short source summary

The context may include compact excerpts such as candidate IDs, statuses,
dimension counts, verdict IDs, and no-trade metadata. It must not create new
calculated metrics.

## Integration

`src.candidate_comparison.write_candidate_comparison_outputs()` writes
`ai_commentary_context.json` after:

1. `current_vs_candidate.json`
2. `selection_decision.json`
3. `action_plan.json`
4. `decision_verdict.json`

Monitoring is integrated later in the product flow. If `monitoring_diff.json`
is not available at context build time, future commentary must state monitoring
context is absent instead of inventing a "what changed" narrative.

## Non-goals

- no LLM invocation
- no prompt template for a provider
- no new scoring or optimizer calculation
- no JSON field renames in existing artifacts
- no replacement of `selection_decision.json`
- no generated report/PDF wording changes in this session

## Relationship to deterministic report commentary

`commentary.txt`, `stress_commentary.txt`, and decision-package summary text are produced by
deterministic report modules (`src/portfolio_commentary.py`, `src/decision_package_reporting.py`).
They are English narrative exports over structured evidence, not the target AI Commentary product
layer and not LLM output.

Product docs must not describe those files as proof that generated AI Commentary already exists.
The Core MVP bundle includes `ai_commentary_context.json` as the current AI Commentary contract:
grounding and guardrails only.

## Future work (not current implementation)

Natural-language AI Commentary generation requires a separate approved spec before implementation.
That future contract must define at minimum:

- provider and prompt policy
- allowed/forbidden inputs (must consume `ai_commentary_context.json`)
- output artifact name and schema
- evidence citation requirements per claim
- tests that block metric invention, verdict fabrication, and trade instructions

Until that spec exists, active docs must state **grounding context only** for AI Commentary.
Track the backlog item in [../ROADMAP.md](../ROADMAP.md) (`RM-ARCH-010`).

## Verification

Required focused checks:

```bash
python -m pytest tests/test_ai_commentary_context.py
python -m pytest tests/test_decision_verdict.py tests/test_current_vs_candidate.py
python run_portfolio_review.py --dry-run
```

Use `scripts/verify_docs.py` for documentation link checks. If archived legacy
documentation has stale links, record the failure as unrelated unless the task
explicitly targets archive repair.
