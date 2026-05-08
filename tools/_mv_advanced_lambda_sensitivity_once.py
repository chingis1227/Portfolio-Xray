"""
One-off: set minimum_variance_turnover_lambda in config.yml, run advanced MV, archive outputs.
Restore config.yml from backup file (argv[2]) after the run.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def inject_lambda(yaml_text: str, lam: float) -> str:
    line = f"minimum_variance_turnover_lambda: {lam}"
    if re.search(r"^minimum_variance_turnover_lambda\s*:", yaml_text, re.MULTILINE):
        return re.sub(
            r"^minimum_variance_turnover_lambda\s*:.*$",
            line,
            yaml_text,
            flags=re.MULTILINE,
        )
    return yaml_text.rstrip() + "\n\n" + line + "\n"


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "usage: _mv_advanced_lambda_sensitivity_once.py LAMBDA BACKUP_YAML_PATH",
            file=sys.stderr,
        )
        raise SystemExit(2)
    lam = float(sys.argv[1])
    backup_path = Path(sys.argv[2])
    backup = backup_path.read_text(encoding="utf-8")

    cfg_path = ROOT / "config.yml"
    cfg_path.write_text(inject_lambda(backup, lam), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(ROOT / "run_minimum_variance_advanced.py")],
        cwd=str(ROOT),
        check=True,
    )

    tag = str(lam).replace(".", "p")
    arch = ROOT / "analysis_mv_lambda_sensitivity" / f"lambda_{tag}"
    arch.mkdir(parents=True, exist_ok=True)
    src = ROOT / "minimum variance advanced portfolio"
    for name in (
        "summary.json",
        "baseline_weights_metadata.json",
        "stress_report.json",
        "weights.json",
    ):
        p = src / name
        if p.is_file():
            shutil.copy2(p, arch / name)

    cfg_path.write_text(backup, encoding="utf-8")
    print(f"OK lambda={lam} archived to {arch}")


if __name__ == "__main__":
    main()
