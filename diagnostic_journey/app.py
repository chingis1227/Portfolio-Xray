"""
Blocks 1–3 diagnostic journey (guided UX draft).

Usage:
    pip install flask pyyaml
    python diagnostic_journey/app.py

Open http://localhost:5006

Reads ``{output_dir_final}/analysis_subject/`` JSON contracts (site_api / core review).
Styling: DESIGN.md via shared ``config_ui/static/design.css``.
"""

from __future__ import annotations

import sys
from pathlib import Path

JOURNEY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = JOURNEY_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from flask import Flask, render_template, send_file

from diagnostic_journey.view_model import build_diagnostic_journey_view_model

app = Flask(
    __name__,
    static_folder=str(JOURNEY_DIR / "static"),
    template_folder=str(JOURNEY_DIR / "templates"),
)

CONFIG_PATH = PROJECT_ROOT / "config.yml"
DESIGN_CSS = PROJECT_ROOT / "config_ui" / "static" / "design.css"


def _read_yaml_config() -> dict:
    if not CONFIG_PATH.is_file():
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _subject_dir() -> Path:
    raw = _read_yaml_config()
    try:
        from src.client_profiles import apply_profile_to_config

        merged = apply_profile_to_config(dict(raw))
    except Exception:
        merged = raw
    name = merged.get("output_dir_final") or "Main portfolio"
    return (PROJECT_ROOT / str(name) / "analysis_subject").resolve()


@app.route("/")
def journey():
    vm = build_diagnostic_journey_view_model(_subject_dir(), project_root=PROJECT_ROOT)
    if not vm.get("has_data"):
        vm["error"] = (
            "No analysis_subject bundle found. Run "
            "`python run_core_diagnostics.py` or `python run_portfolio_review.py` first."
        )
    return render_template(
        "journey.html",
        vm=vm,
        design_css_href="/design-assets/design.css",
    )


@app.route("/design-assets/design.css")
def design_css():
    return send_file(DESIGN_CSS, mimetype="text/css")


def main() -> None:
    print("Portfolio diagnostic UI")
    print("  Open in browser: http://127.0.0.1:5006")
    print("  Stop server: Ctrl+C in this window")
    print("  (Leave this window open while you use the browser.)")
    print()
    app.run(host="127.0.0.1", port=5006, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
