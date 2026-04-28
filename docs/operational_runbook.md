# Operational Runbook

Short guide for **when to run optimization**, **how to handle universe and config changes**, and **how to read run results**. See **production_workflow.md** for status and gate semantics.

---

## 1. When to re-run optimization

Re-run `python run_optimization.py` (from project root; **single-stage** max-return optimizer with weight bounds and soft vol/return targets вЂ” see **docs/portfolio_construction_policy.md**) in these cases:

| Trigger | Action |
|--------|--------|
| **Calendar** | e.g. monthly or quarterly on a fixed date (e.g. first business day of the month). |
| **Deviation** | Current or last-rebalance weights have drifted from target (e.g. max \|w_current в€’ w_target\| > 2% or sum of \|О”w\| > 5%). Consider rebalancing and/or re-running optimization. |
| **Universe change** | Any add/remove of tickers in **config.yml** в†’ full re-run (see В§2). |
| **Profile / mandate change** | Change of **client_profile**, **target_vol_annual**, **target_max_drawdown_pct**, or other policy fields в†’ full re-run. |
| **Stress diagnostics** | `DIAG_ATTENTION` or `FAIL_STRESS` (informational) in violations в†’ optional PM review; does not prevent release. Re-run only if you change architecture. |

---

## 2. Universe changes (add/remove tickers)

- **Adding a ticker:** Add it to `config.yml` (`tickers`). Then run a **full** optimization. Do not try to вЂњpatchвЂќ existing weights; the new weights file will include the new ticker.
- **Removing a ticker:** Remove from `config.yml`, then run a **full** optimization. The new `portfolio_weights.yml` will no longer contain the removed ticker (weight 0 or omitted).

There is no partial update: every change to the investable universe requires a full re-run of `run_optimization.py`.

---

## 3. How to read run_result.json

After each run, check `output_dir_final/run_result.json` (e.g. **Main portfolio/run_result.json**):

| Field | Meaning |
|-------|--------|
| **status** | **APPROVED**, **OK_FALLBACK**, or **FAIL_*** (see **production_workflow.md**). |
| **weights** | Target weights (empty if a blocking FAIL_* prevented writing weights). |
| **violations** | List of `{ "code", "details" }` (e.g. mandate, data, stress as **VIOL_FAIL_STRESS** with `diagnostic_only`; see code). |
| **next_actions** | Suggested next steps when violations or failures occur. |
| **resolved_config** | Merged config (profile + overrides) used for the run; for audit and reproducibility. |

If **status** is **FAIL_DATA** or **FAIL_MANDATE** в†’ weights were not written; follow **next_actions** and fix config/data or mandate before using the system for allocation.

If **status** is **APPROVED** or **OK_FALLBACK** в†’ weights were written to `portfolio_weights.yml`; use them as target weights, taking into account **violations** (e.g. stress diagnostics, young-ETF warnings) as per your mandate.

---

## 4. Output files

| File | Location | Purpose |
|------|----------|--------|
| **portfolio_weights.yml** | output_dir_final (e.g. Р¤РРќРђР›Р¬РќР«Р• Р Р•Р—РЈР›Р¬РўРђРўР«) | Target weights for execution; only present if weights were written. |
| **run_result.json** | output_dir_final | Status, violations, next_actions, resolved_config; always written after a run. |
| **snapshot.json** | output_dir_final | Snapshot of weights, RC, constraints, stress summary; written when weights are written. |
| **ips_summary.txt** | output_dir_final | One-page mandate summary and actions by status; written after every run. |

Report CSV and other report outputs are produced by `run_report.py` (invoked after optimization when report is enabled). If report fails, weights and run_result are still saved.

---

## 5. First run (РїРµСЂРІС‹Р№ РґРµРїР»РѕР№)

1. **РџСЂРѕРІРµСЂРёС‚СЊ config.yml:** Р·Р°РґР°РЅС‹ `tickers`, `client_profile`, `investor_currency`. РџСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё Р·Р°РґР°С‚СЊ `liquidity_need_months`, `monthly_expenses`, `portfolio_value` РґР»СЏ СЂР°СЃС‡С‘С‚Р° Р»РёРєРІРёРґРЅРѕРіРѕ РїРѕР»Р°.
2. **Р—Р°РїСѓСЃРє:** РёР· РєРѕСЂРЅСЏ РїСЂРѕРµРєС‚Р° РІС‹РїРѕР»РЅРёС‚СЊ `python run_optimization.py` (РїСЂРё РїРµСЂРІРѕР№ Р·Р°РіСЂСѓР·РєРµ РґР°РЅРЅС‹С… РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ `--no-cache`).
3. **РџСЂРѕРІРµСЂРєР° СЂРµР·СѓР»СЊС‚Р°С‚Р°:** РѕС‚РєСЂС‹С‚СЊ `output_dir_final/run_result.json` Рё РїСЂРѕРІРµСЂРёС‚СЊ РїРѕР»Рµ **status**. РџСЂРё **APPROVED** РёР»Рё **OK_FALLBACK** РІРµСЃР° Р·Р°РїРёСЃР°РЅС‹ РІ `portfolio_weights.yml` Рё РјРѕРіСѓС‚ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊСЃСЏ РєР°Рє С†РµР»РµРІС‹Рµ (РїСЂРё OK_FALLBACK вЂ” РїСЂРѕРІРµСЂРёС‚СЊ **rc_breaches**).
4. **РџСЂРё РЅР°СЂСѓС€РµРЅРёСЏС…:** СЃР»РµРґРѕРІР°С‚СЊ **next_actions**. РџСЂРё **FAIL_MANDATE** вЂ” РёСЃС‚РѕСЂРёС‡РµСЃРєР°СЏ РїСЂРѕСЃР°РґРєР° РЅР° РїРѕР»РЅРѕР№ РІС‹Р±РѕСЂРєРµ РЅРµ РїСЂРѕС€Р»Р° Р»РёРјРёС‚ (РёР»Рё РЅРµС‚ РґР°РЅРЅС‹С…); СЃРєРѕСЂСЂРµРєС‚РёСЂРѕРІР°С‚СЊ СЂРёСЃРє/РјР°РЅРґР°С‚ Рё РїРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ. РЎС‚СЂРµСЃСЃ **DIAG_*** РЅРµ Р±Р»РѕРєРёСЂСѓРµС‚ РІС‹РїСѓСЃРє.

---

## 6. Recurring run (СЂРµРіСѓР»СЏСЂРЅС‹Р№ РїСЂРѕРіРѕРЅ)

1. **РћР±РЅРѕРІР»РµРЅРёРµ РґР°РЅРЅС‹С…:** РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё Р·Р°РїСѓСЃРєР°С‚СЊ СЃ С„Р»Р°РіРѕРј `--no-cache` РґР»СЏ РїРµСЂРµР·Р°РіСЂСѓР·РєРё С†РµРЅ Рё РєСѓСЂСЃРѕРІ.
2. **РљР°Р»РµРЅРґР°СЂРЅС‹Р№ Р·Р°РїСѓСЃРє:** РІС‹РїРѕР»РЅСЏС‚СЊ `run_optimization.py` РїРѕ РІС‹Р±СЂР°РЅРЅРѕРјСѓ РіСЂР°С„РёРєСѓ (РЅР°РїСЂРёРјРµСЂ, РїРµСЂРІС‹Р№ СЂР°Р±РѕС‡РёР№ РґРµРЅСЊ РјРµСЃСЏС†Р°).
3. **РЎСЂР°РІРЅРµРЅРёРµ СЃ РїСЂРµРґС‹РґСѓС‰РёРј РїСЂРѕРіРѕРЅРѕРј:** РїСЂРѕРІРµСЂРёС‚СЊ СЃС‚Р°С‚СѓСЃ Рё РЅР°СЂСѓС€РµРЅРёСЏ РІ РЅРѕРІРѕРј run_result.json; РїСЂРё РёР·РјРµРЅРµРЅРёРё СЃС‚Р°С‚СѓСЃР° РёР»Рё РїРѕСЏРІР»РµРЅРёРё РЅРѕРІС‹С… РЅР°СЂСѓС€РµРЅРёР№ вЂ” РїСЂРѕСЃРјРѕС‚СЂРµС‚СЊ **next_actions** Рё РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё СЃРєРѕСЂСЂРµРєС‚РёСЂРѕРІР°С‚СЊ РєРѕРЅС„РёРі РёР»Рё РјР°РЅРґР°С‚.
4. **Р РµР±Р°Р»Р°РЅСЃ:** РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ СЃРїРёСЃРєР° СЃРґРµР»РѕРє РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ `run_rebalance.py --current current_positions.yml --target <path_to_portfolio_weights.yml>`. РџСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё Р·Р°РґР°С‚СЊ РїРѕСЂРѕРі СЂРµР±Р°Р»Р°РЅСЃР° (`--threshold`) Рё РјРёРЅРёРјР°Р»СЊРЅС‹Р№ СЂР°Р·РјРµСЂ СЃРґРµР»РєРё (`--min-trade`). РЈС‡РёС‚С‹РІР°С‚СЊ РѕР±СЉС‘Рј С‚РѕСЂРіРѕРІР»Рё (turnover) РїСЂРё РїСЂРёРЅСЏС‚РёРё СЂРµС€РµРЅРёСЏ Рѕ РїСЂРѕРІРµРґРµРЅРёРё СЂРµР±Р°Р»Р°РЅСЃР°.
