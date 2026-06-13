---
description: Run the selected variant and show only the stress result
---

Run a stress-only pass for the selected portfolio variant.

Requirements:
1) Determine the variant:
   - if the user explicitly specified `equal-weight`, `risk-parity`, or `main`, use it;
   - if not specified, ask one concise clarification question with those three options.

2) Run:
   - `python run_stress_variant.py --variant <equal-weight|risk-parity|main>`
   - if the user explicitly asks to bypass cache, run:
     - `python run_stress_variant.py --variant <...> --no-cache`

3) After completion, show only the stress block:
   - status
   - reason (`fail_reason_code` / `warning_code`)
   - `worst_scenario_loss_pct`
   - `failed_scenario`
   - `failed_test`
   - `factor_betas_5y`
   - `factor_betas_10y`
   - scenarios: `scenario_id`, `pnl`, `pass`, `top1_rc`, `top3_rc_sum`

4) If the run fails:
   - show the error code
   - briefly show the tail of stdout/stderr
   - suggest the next step.
