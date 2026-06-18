# Diagnostic Case File UX Design

Date: 2026-06-18
Status: Approved for implementation in this session
Scope: frontend information hierarchy, UI copy, route block order, documentation sync, and visual QA expectations for Portfolio MRI's current 8-step platform journey.

## Purpose

Portfolio MRI must read like a diagnostic case file, not a generic dashboard or optimizer cockpit. Each screen should answer the investor's next question before showing metrics. Metrics stay in the product, but promoted metrics must explain investor meaning: what problem they reveal, why it matters, or what would change the next decision.

This design changes frontend presentation only. It does not change backend schemas, formulas, generated artifact semantics, candidate factory behavior, or route unlock logic.

## Shared screen rhythm

Every analytical route uses this first-read hierarchy:

1. Main finding / investment conclusion.
2. Why it matters.
3. Key evidence, capped at three to five facts.
4. Metrics with investor meaning.
5. Collapsed drill-down for technical evidence, provenance, warnings, and full matrices.
6. Next safe decision.

Primary UI must not lead with vague operational states such as Evidence available, Evidence unavailable, Current portfolio only, Diagnostic only, No rebalancing, Comparison pending, Unavailable, or Evidence required. Those states may appear only as compact secondary status, limitation detail, or a specific explanation of what conclusion is blocked and what the user should do next.

## Visual direction

The existing DESIGN.md direction remains authoritative: restrained dark decision room, flat case-file panels, hairline borders, sparse badges, no glassy dashboard wall, no optimizer-first language, no new visual theme. Motion should stay subtle and purposeful. Buttons and interactive cards should feel responsive without becoming playful; use short transform/opacity transitions only where they clarify press or reveal state.

## Route designs

### /portfolio-input

New order:

1. Portfolio to diagnose.
2. Input readiness.
3. Client Fit context.
4. Holdings and weights.
5. Collapsed saved portfolios / recovery / technical validation details.
6. Run diagnosis.

Top cards:

- Portfolio to diagnose.
- Input readiness.
- Client Fit context.

Top-layer metrics:

- holdings count;
- total weight;
- investor currency;
- Client Fit profile presence.

Move to drill-down:

- saved portfolios;
- recover by review reference;
- staged progress internals;
- technical validation details.

Remove or compress:

- current-allocation-only as a large primary message;
- any operator-style recovery explanation above the first-read input answer.

User should understand: I have defined the current portfolio that Portfolio MRI will diagnose.

Forbidden primary UI words: optimizer target, suitability approval, raw review id, backend, staged status table.

### /diagnosis

New order:

1. Main diagnosis.
2. Why it matters.
3. Key evidence.
4. Metrics with investor meaning.
5. Collapsed advanced diagnostics.
6. Next decision: open Stress Lab.

Top cards:

- Main diagnosis.
- Why it matters.
- Key evidence.

Top-layer metrics:

- primary issue;
- main exposure;
- concentration;
- worst observed downside;
- evidence confidence or quality.

Move to drill-down:

- full MetricMatrix;
- VaR, ES, skewness, kurtosis, beta, Treynor, Sharpe, Sortino;
- provenance;
- technical limitations;
- full X-Ray panels.

Remove or compress:

- utility text that says current only as the main answer;
- repeated evidence badges;
- MetricMatrix before the diagnosis is understood.

User should understand: This is the current portfolio's main problem and why it is investment-relevant.

Forbidden primary UI words: rebalance recommendation, diagnostic only as the headline, raw evidence chain, artifact names.

### /evidence

New order:

1. Stress failure mode.
2. Worst scenario.
3. Loss drivers and protection gap.
4. Stress metrics with investor meaning.
5. Collapsed scenario library, factor detail, and limitations.
6. Next decision: continue to Client Fit.

Top cards:

- Stress failure mode.
- Worst scenario.
- Loss drivers and protection gap.

Top-layer metrics:

- worst scenario;
- estimated stress loss;
- top loss drivers;
- hedge/protection gap;
- evidence confidence.

Move to drill-down:

- scenario library;
- factor attribution;
- selected scenario details;
- evidence trace;
- data limitations.

Remove or compress:

- unavailable as the primary result;
- candidate, verdict, or rebalance language.

User should understand: I can see where the current portfolio breaks in a bad market.

Forbidden primary UI words: candidate comparison, rebalance, trade, raw scenario ids.

### /client-fit

New order:

1. Fit interpretation.
2. Main mismatch.
3. Profile context.
4. Profile metrics with investor meaning.
5. Collapsed raw profile answers and compatibility detail.
6. Next decision: continue to Hypothesis.

Top cards:

- Fit interpretation.
- Main mismatch.
- Profile context.

Top-layer metrics:

- drawdown tolerance vs portfolio downside;
- horizon context;
- target or volatility mismatch only if meaningful;
- profile source quality.

Move to drill-down:

- full target rows;
- raw profile answers;
- compatibility details;
- evidence provenance.

Remove or compress:

- Evidence required as a top badge;
- repeated aligned/outside badges;
- any phrasing that profile fit clears a material portfolio issue.

User should understand: This risk either fits or conflicts with the stated profile, but this is not suitability approval.

Forbidden primary UI words: suitability approved, safe, proof no action is needed, optimizer mandate.

### /hypothesis

The route remains one MVP route, but it is visibly split into four sections.

Section 1: Problem Classification
Top cards:

- Named problem.
- Severity and confidence.
- Evidence behind classification.

Section 2: Candidate Launchpad
Top cards:

- Investment hypothesis.
- Mathematical method.
- Why this method fits the problem.

Section 3: Alternatives Builder
Top cards:

- Test setup.
- Success criteria.
- Trade-off to watch.

Section 4: Candidate Generation Result
Top cards:

- Candidate created or failed.
- Method used.
- Ready for comparison.

Top-layer metrics:

- problem severity;
- problem confidence;
- selected investment hypothesis;
- selected mathematical method, such as Minimum CVaR;
- first success criterion;
- main trade-off.

Move to drill-down:

- other tests;
- monitor/data paths;
- method internals;
- min/max asset weight;
- capped/uncapped settings;
- developer details.

Remove or compress:

- action console as the dominant first read;
- generated weights as primary answer;
- backend lineage ids as visible proof.

User should understand: I understand the problem, hypothesis, mathematical method, and exactly what will be tested.

Forbidden primary UI words: recommended allocation, best candidate, trade, auto-generate, factory id.

### /comparison

New order:

1. What improved.
2. What worsened.
3. Is the trade-off meaningful?
4. Comparison metrics with investor meaning.
5. Collapsed allocation tables and technical notes.
6. Next decision: continue to Verdict.

Top cards:

- What improved.
- What worsened.
- Is the trade-off meaningful?

Top-layer metrics:

- main improvement;
- main cost or trade-off;
- materiality;
- Client Fit impact if meaningful;
- evidence confidence.

Move to drill-down:

- allocation tables;
- full comparison matrix;
- warnings;
- technical notes.

Remove or compress:

- comparison pending as top evidence quality;
- current/candidate inventory as the first answer;
- winner framing.

User should understand: The candidate improves X, worsens Y, and the materiality is clear enough for a verdict step or not.

Forbidden primary UI words: winner, switch, recommended, best portfolio, final verdict.

### /verdict

New order:

1. Decision stance.
2. Reason.
3. What would change the verdict.
4. Verdict metrics with investor meaning.
5. Collapsed rationale, provenance, and limitations.
6. Next decision: open Report or test another hypothesis.

Allowed decision stances:

- Keep current.
- Review rebalance.
- Test another candidate.
- Evidence insufficient.

Top cards:

- Decision stance.
- Reason.
- What would change the verdict.

Top-layer metrics:

- decision status;
- confidence;
- main evidence;
- main limitation;
- next action.

Move to drill-down:

- full rationale;
- provenance;
- detailed limitations;
- lineage details.

Remove or compress:

- unavailable as a headline;
- generated verdict mechanics;
- any language that implies trade execution.

User should understand: The next safe action is to keep current, review a rebalance, test another candidate, or avoid conclusion because evidence is insufficient.

Forbidden primary UI words: trade now, best portfolio, recommended portfolio, suitability approved, safe, guaranteed improvement.

### /report

New order:

1. Plain-English explanation.
2. Evidence used.
3. Limitations.
4. Narrative preview.
5. Collapsed grounding trace and unavailable evidence.
6. Next decision: read/share preview or return to Verdict.

Top cards:

- Plain-English explanation.
- Evidence used.
- Limitations.

Top-layer metrics:

- main diagnosis;
- stress evidence;
- comparison result;
- verdict stance.

Move to drill-down:

- full evidence used;
- unavailable evidence;
- warnings;
- report generation internals.

Remove or compress:

- report grounding trace above the narrative;
- every metric repeated from prior pages;
- raw provenance as primary proof.

User should understand: This is how to explain the full evidence chain in simple investment language.

Forbidden primary UI words: unsupported AI recommendation, raw artifact viewer, polished PDF as default output.

## Implementation notes

Use existing compact review summaries first. Do not invent formulas or backend-derived meanings. If a field is missing, state what conclusion is blocked and what the user can do next. Update shared route copy and presentation components before adding new one-off patterns. Keep drill-downs collapsed unless the route already requires the detail to be visible for a safe next action.

## Testing and acceptance

Implementation is complete only when:

- primary route cards do not lead with generic availability states;
- top-layer metrics include investor-facing explanations or takeaways;
- candidate language shows both investment hypothesis and mathematical method;
- verdict language stays within the allowed stances and avoids advice/execution language;
- docs match code structure;
- frontend lint/typecheck are run when available;
- changed routes are visually checked at desktop and mobile widths or the unverified routes are explicitly reported with blockers.
