# Portfolio Optimization вЂ” РµРґРёРЅР°СЏ С‚РѕС‡РєР° РІС…РѕРґР°

РЎРёСЃС‚РµРјР° СЃС‚СЂРѕРёС‚ РїРѕСЂС‚С„РµР»СЊ **РѕРґРЅРѕСЃС‚Р°РґРёР№РЅРѕР№** РѕРїС‚РёРјРёР·Р°С†РёРµР№ (РјР°РєСЃРёРјРёР·Р°С†РёСЏ РѕР¶РёРґР°РµРјРѕР№ РґРѕС…РѕРґРЅРѕСЃС‚Рё РїСЂРё РјСЏРіРєРёС… С†РµР»СЏС… РїРѕ РІРѕР»Р°С‚РёР»СЊРЅРѕСЃС‚Рё/РґРѕС…РѕРґРЅРѕСЃС‚Рё Рё РѕРіСЂР°РЅРёС‡РµРЅРёСЏС… РїРѕ **РІРµСЃСѓ**), Р·Р°С‚РµРј ProLiquidity Рё РґРёР°РіРЅРѕСЃС‚РёС‡РµСЃРєРёР№ СЃС‚СЂРµСЃСЃ. **RC_vol** РІ РѕС‚С‡С‘С‚Р°С… вЂ” РґРёР°РіРЅРѕСЃС‚РёРєР°, РЅРµ Р¶С‘СЃС‚РєРёР№ constraint. Р’РµСЃР° РІС‹РґР°С‘С‚ С‚РѕР»СЊРєРѕ РѕРїС‚РёРјРёР·Р°С‚РѕСЂ; СЂСѓС‡РЅР°СЏ РїСЂР°РІРєР° РІРµСЃРѕРІ РІ РєРѕРЅС„РёРіРµ РЅРµ РґРѕРїСѓСЃРєР°РµС‚СЃСЏ (РёСЃРєР»СЋС‡РµРЅРёРµ вЂ” РїСЂРѕС‚РѕРєРѕР» В«View After OptimizationВ»).

---

## РџР°Р№РїР»Р°Р№РЅ

1. **РћРїС‚РёРјРёР·Р°С†РёСЏ**
   ```bash
   python run_optimization.py [--no-cache] [--write-config]
   ```
   Р§РёС‚Р°РµС‚ `config.yml` Рё РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё **`../config/client_profiles.yml`** (РїСѓС‚СЊ РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅРѕ РєРѕСЂРЅСЏ СЂРµРїРѕР·РёС‚РѕСЂРёСЏ); Р·Р°РіСЂСѓР¶Р°РµС‚ РґР°РЅРЅС‹Рµ; РѕРґРёРЅ РїСЂРѕС…РѕРґ РѕРїС‚РёРјРёР·Р°С‚РѕСЂР° + ProLiquidity. РџРёС€РµС‚ **`portfolio_weights.yml`** Рё **`run_result.json`** РІ **`output_dir_final`** (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ **Main portfolio**). РџСЂРё РїСЂРѕРІР°Р»Рµ РјР°РЅРґР°С‚Р° MaxDD вЂ” **FAIL_MANDATE**, РІРµСЃР° РЅРµ Р·Р°РїРёСЃС‹РІР°СЋС‚СЃСЏ.

2. **РћС‚С‡С‘С‚**
   ```bash
   python run_report.py [--no-cache] [--clear-cache] [--backtest-mode dynamic_nan_safe]
   ```
   Р‘РµСЂС‘С‚ РІРµСЃР° РёР· РєРѕРЅС„РёРіР° РёР»Рё РёР· **`portfolio_weights.yml`**; РјРµС‚СЂРёРєРё 3Y/5Y/10Y, RC_vol, СЃС‚СЂРµСЃСЃ; CSV РІ `results_csv/`, РѕС‚С‡С‘С‚С‹ РІ `output_dir_final`.

**РџРѕСЂСЏРґРѕРє:** СЃРЅР°С‡Р°Р»Р° `run_optimization.py`, Р·Р°С‚РµРј `run_report.py`.

---

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|------|------------|
| **config.yml** | РўРёРєРµСЂС‹, РІР°Р»СЋС‚Р°, РїСЂРѕС„РёР»СЊ, Р»РёРєРІРёРґРЅРѕСЃС‚СЊ, cash_policy, target_vol, target_max_drawdown_pct, РѕРєРЅР°, `output_dir_final`. |
| **assets.yml** | РњРµС‚Р°РґР°РЅРЅС‹Рµ Р°РєС‚РёРІРѕРІ. РћРїС†РёРѕРЅР°Р»СЊРЅРѕ. |


---

## Р”РѕРєСѓРјРµРЅС‚Р°С†РёСЏ (РёСЃС‚РѕС‡РЅРёРєРё РёСЃС‚РёРЅС‹)

РџСѓС‚Рё РЅРёР¶Рµ вЂ” РѕС‚ **РєРѕСЂРЅСЏ СЂРµРїРѕР·РёС‚РѕСЂРёСЏ** (РїР°РїРєР° СЃ `run_optimization.py`):

- [Portfolio Construction Policy](../docs/portfolio_construction_policy.md)
- [Metrics Specification](../metrics_specification.md)
- [Data policy, NaN, young ETFs](../docs/data_policy_nan_young_etfs.md)
- [Feasibility constraints](../docs/docs/feasibility_constraints_spec.md)
- [Optimization run checks](../docs/optimization_run_checks.md)
- [Stress testing spec](../docs/docs/stress_testing_spec.md)
- [Production workflow](../docs/production_workflow.md)
- [View After Optimization](../docs/docs/view_after_optimization_spec.md)

---

## Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ

- **View After Optimization:** `run_view_after_optimization.py`.
- **РњР°РЅРґР°С‚ MaxDD:** С‚РѕР»СЊРєРѕ **СЂРµР°Р»РёР·РѕРІР°РЅРЅР°СЏ** РїСЂРѕСЃР°РґРєР° РЅР° РїРѕР»РЅРѕР№ РїРµСЂРµСЃРµРєР°СЋС‰РµР№СЃСЏ РёСЃС‚РѕСЂРёРё в†’ **FAIL_MANDATE**; СЃС‚СЂРµСЃСЃ **DIAG_*** РЅРµ Р±Р»РѕРєРёСЂСѓРµС‚ РІС‹РїСѓСЃРє РІРµСЃРѕРІ РїСЂРё СѓСЃРїРµС€РЅРѕРј РјР°РЅРґР°С‚Рµ.
