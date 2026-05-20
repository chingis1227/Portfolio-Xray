# Proposals Register

This directory holds **reviewable methodology proposals** that are not yet (or may never be)
implemented in code. Proposals do not override `docs/specs/*.md`, `SPEC.md`, or runtime behavior
until accepted in [DECISIONS.md](../../DECISIONS.md) and reflected in the owning spec.

## Status Values

| Status | Meaning |
| --- | --- |
| Draft | Under review; no decision recorded. |
| Accepted | Decision recorded; implementation may follow in a dedicated session. |
| Deferred | Decision recorded; implementation explicitly postponed. |
| Superseded | Replaced by a later proposal or spec change. |

## Register

| Date | Proposal | Status | Decision | ExecPlan / RM |
| --- | --- | --- | --- | --- |
| 2026-05-20 | [Crypto and volatility synthetic stress scenarios](2026-05-20_crypto_vol_stress_scenarios_proposal.md) | Deferred | [DEC-2026-05-20-002](../../DECISIONS.md) | Block 3 Session 08, `RM-959` |

## Maintenance

- Link each proposal from the active ExecPlan session that created it.
- When a proposal is implemented, move canonical rules into the owning spec and mark the proposal
  **Superseded** or **Accepted** with an implementation note.
- Do not add scenarios to `src/stress.py::SCENARIOS` without an accepted decision and spec update.
