# Block 2.6 Portfolio Weakness Map — ExecPlan

**Status: Completed** (Session 08 closed 2026-05-26). Prerequisite: [Block 2.5 Risk Budget View MVP](2026-05-26_block_2_5_risk_budget_view_plan.md) **Completed**; Blocks 2.1–2.5 **Completed**. Evidence: [Block 2.6 acceptance audit](../audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md); closure pytest **35 passed**; live `run_portfolio_review.py` on root `config.yml` with nine risk types on subject X-Ray.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows [PLANS.md](../../PLANS.md) from the repository root. A future contributor should continue from this file alone without prior chat context.

## Purpose / Big Picture

Сейчас Core MVP заканчивается на **Block 2.5** ([`block_2_5_risk_budget_view`](../exec_plans/2026-05-26_block_2_5_risk_budget_view_plan.md)). Карта уязвимостей уже **частично реализована как legacy** `sections.weakness_map` в [`src/portfolio_xray.py`](../../src/portfolio_xray.py) (`_weakness_map_section`, ~L3197), но:

- это **не product block** (в diagnostics spec — §2.7 advanced/legacy);
- читает **`stress_report` напрямую** (scenario PnL, `pnl_by_asset_pct`) — это зона Stress Lab, не pre-check карты слабостей;
- severity = `low/medium/high` через threshold aggregation, **без numeric score 0–100** и weighted client explanation как в пользовательском брифе.

**Цель Block 2.6:** top-level `block_2_6_portfolio_weakness_map` на `{output_dir_final}/analysis_subject/portfolio_xray.json`, который отвечает: *«где портфель потенциально слаб и какие сценарии проверить дальше»* — **не** «сколько портфель потеряет». Stress Lab уже после этого делает фактический crash test и loss attribution.

## Progress

- [x] (2026-05-26) **Session 00 — ExecPlan foundation (this file):** сформирован план работы по Block 2.6, зафиксирована жёсткая граница со Stress Lab (без чтения `stress_report` в продуктовом блоке), описаны входы из блоков 2.1–2.5 и перечень девяти risk types; план зарегистрирован как Active в [docs/exec_plans/README.md](README.md).
- [x] (2026-05-26) **Session 01 — Product contract (docs):** §2.6.1 в diagnostics spec, Core MVP 2.1–2.6, Archetype §2.7 legacy, `DEC-2026-05-26-006`, SPEC/OUTPUTS/GLOSSARY.
- [x] (2026-05-26) **Sessions 02–04 — Module + scoring:** `src/block_2_6_portfolio_weakness_map.py`, `RISK_RULE_TABLES`, `heuristic_v1`, unit tests.
- [x] (2026-05-26) **Session 05 — Wiring:** `build_portfolio_xray_v2` after Block 2.5; legacy `sections.weakness_map` unchanged.
- [x] (2026-05-26) **Sessions 06–07 — Golden + pipeline:** golden v2, contract tests, `product_bundle_paths`, `live_full_e2e`, MVP smoke.
- [x] (2026-05-26) **Session 08 — Live validation + closure:** live run root `config.yml`, [acceptance audit](../audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md), CHANGELOG, plan **Completed**.

## Surprises & Discoveries

- Observation: Legacy `weakness_map` уже сейчас агрегирует stress/factor/tail evidence, но ближе к severity-листу, чем к диагностической карте уязвимостей с явной моделью scoring и объяснимыми весами.
  Evidence: `_weakness_map_section` в `src/portfolio_xray.py` (~L3197–L3305), использование `WEAKNESS_SCENARIO_MAP`, `WEAKNESS_FACTOR_KEYS_BY_RISK`, `scenario_coverage`, `top_asset_loss_drivers`, `top_factor_drivers`.

- Observation: В diagnostics spec (§2.7) Weakness Map описан как advanced/legacy-section, продуктовый contract для Block 2.6 отсутствует; Core MVP product diagnosis сегодня заканчивается на Block 2.5.
  Evidence: [docs/specs/portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) Scope table (2.6 Archetype, 2.7 Weakness Map — No / legacy).

- Observation: Все необходимые сигналы для user-брифа по Equity Crash Risk уже есть в блоках 2.1–2.5 и threshold registry.
  Evidence: downside_beta и beta_portfolio в `src/block_2_2_portfolio_metrics.py`; `beta_eq` и factor variance contribution в `src/block_2_3_factor_exposure.py`; equity RC bucket в `src/block_2_5_risk_budget_view.py`; allocation по main_risk_factor в `src/block_2_1_asset_allocation.py`; thresholds в `XRAY_THRESHOLDS` (`portfolio_xray_diagnostics_spec` / `portfolio_xray.py`).

## Decision Log

- Decision: Product Block 2.6 = **Portfolio Weakness Map** (`block_2_6_portfolio_weakness_map`), поверх legacy `sections.weakness_map`.
  Rationale: логичный следующий шаг после Block 2.5, итоговая карта уязвимостей, агрегирующая сигналы 2.1–2.5; legacy section остаётся для совместимости и Problem Classification.
  Date/Author: 2026-05-26 / Session 00.

- Decision: Жёсткая граница со Stress Lab — Block 2.6 **не читает** `stress_report` и не использует scenario PnL / pass-fail / loss contributors / `pnl_by_asset_pct`.
  Rationale: роль блока до стресса — указать, где слабость вероятна и какие сценарии проверять, а не считать фактический убыток; Stress Lab владеет loss, pass/fail и hedge gap.
  Date/Author: 2026-05-26 / Session 00.

- Decision: Входы для Block 2.6 — только product blocks 2.1–2.5 (и, при необходимости, summary из Block 1), без прямого чтения snapshot/stress artifacts.
  Rationale: соблюдение X-Ray layer границы; повторное использование уже нормализованных product contracts, минимизация дублирования логики.
  Date/Author: 2026-05-26 / Session 00.

- Decision: Crypto shock (`crypto_shock`) остаётся только в legacy weakness-map; продуктовый Block 2.6 использует ровно девять risk types из пользовательского брифа.
  Rationale: требование пользователя — контролируемый список из девяти рисков в MVP; crypto-логика считается advanced/расширением.
  Date/Author: 2026-05-26 / Session 00.

## Outcomes & Retrospective

**Session 00:** Зафиксирована цель Block 2.6, девять risk types, inputs 2.1–2.5, stress boundary vs Stress Lab.

**Sessions 01–07:** Product contract (`DEC-2026-05-26-006`), модуль `block_2_6_portfolio_weakness_map`, wiring в `build_portfolio_xray_v2`, golden/contract/pipeline gates.

**Session 08 (2026-05-26):** Live `run_portfolio_review.py` на root `config.yml` (diagnosis + `equal_weight`); subject X-Ray несёт `block_2_6_portfolio_weakness_map` с девятью risk types (8 scored, `usd_shock` unavailable); stress keys отсутствуют в product block; legacy `sections.weakness_map` сохранён; pytest closure **35 passed**; validator **PASS**. ExecPlan **Completed** — evidence: [acceptance audit](../audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md).

## Context and Orientation

- Текущий pipeline: `run_portfolio_review.py` материализует `{output_dir_final}/analysis_subject/portfolio_xray.json` через `build_portfolio_xray_v2` в `src/portfolio_xray.py`.
- Product blocks: сегодня реализованы `block_2_1_asset_allocation`, `block_2_2_portfolio_metrics`, `block_2_3_factor_exposure`, `block_2_4_hidden_exposure`, `block_2_5_risk_budget_view`; legacy sections под `sections.*` включают `weakness_map`.
- Weakness map V2 уже использует factor betas, tail risk, stress scenario coverage и taxonomy, но описан как advanced/legacy и смешивает stress evidence и rule-based aggregation.
- User brief требует product Block 2.6, который:
  - агрегирует сигналы из блоков 2.1–2.5;
  - выдаёт 0–100 score + Low/Medium/High per risk type;
  - объясняет, *почему* риск отмечен как высокий/средний (по аналогии с примером Equity Crash Risk);
  - отдаёт `next_tests` — список сценариев для Stress Lab, без расчёта убытка.

## Plan of Work (Sessions 01–08 — high level)

1. **Session 01 — Product docs:** описать §2.6.1 product контракт в diagnostics spec, обновить layer spec/SPEC/OUTPUTS/PRODUCT/GLOSSARY/DECISIONS; Core MVP = Blocks 2.1–2.6, Archetype/legacy Weakness Map демотированы.
2. **Sessions 02–04 — Module + scoring:** реализовать `block_2_6_portfolio_weakness_map` module (to be added under `src/`) как rule-based adapter над блоками 2.1–2.5, с явными rule tables и scoring engine, плюс unit tests.
3. **Session 05 — Wiring:** подключить новый блок в `build_portfolio_xray_v2` после Block 2.5, сохранив legacy `sections.weakness_map`.
4. **Sessions 06–07 — Golden + pipeline:** обновить golden fixture, contract tests и product bundle discovery; добавить pipeline/E2E проверки на наличие Block 2.6.
5. **Session 08 — Live closure:** прогнать `run_portfolio_review.py` на root `config.yml`, записать acceptance audit с девятью рисками, обновить CHANGELOG и отметить ExecPlan как Completed.

