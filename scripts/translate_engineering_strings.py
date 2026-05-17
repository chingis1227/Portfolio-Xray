"""Replace Russian engineering strings with English in source Python files."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (old, new) — old strings must match UTF-8 on disk exactly.
REPLACEMENTS: list[tuple[str, str]] = [
    (
        "    Важно: эта функция не применяет никакой policy-логики к входным весам.\n"
        "    Для Equal-Weight и Risk-Parity веса должны быть построены как baseline-портфели\n"
        "    без RC caps / weight caps / discretionary overlays\n"
        "    и скрытых policy-фильтров.",
        "    Important: this function does not apply policy logic to input weights.\n"
        "    Equal-Weight and Risk-Parity weights must be built as baseline portfolios\n"
        "    without RC caps / weight caps / discretionary overlays\n"
        "    or hidden policy filters.",
    ),
    ("Валюта инвестора", "Investor currency"),
    ("Базовый бенчмарк", "Base benchmark"),
    ("Локальные бенчмарки", "Local benchmarks"),
    ("Целевая доходность", "Target return"),
    (
        "Нет данных по cash proxy ({cash_proxy_ticker}); для расчёта портфеля используется нулевая доходность кэша.",
        "No data for cash proxy ({cash_proxy_ticker}); portfolio calculation uses zero cash return.",
    ),
    ("Сводка по доступным данным", "Data availability summary"),
    ("нет данных о доходностях", "no return data"),
    ("coverage в окне %d мес.", "coverage in %d-month window"),
    ("Локальный бенчмарк", "Local benchmark"),
    ("не найден", "not found"),
    ("используем базовый бенчмарк", "using base benchmark"),
    ("RC_vol: нет активов для расчёта", "RC_vol: no assets available for calculation"),
    ("недостаточно данных (доступно", "insufficient data ("),
    (" мес.)", " months available)"),
    (
        "portfolio_valid = False только если MaxDD на полной пересекающейся истории нарушает мандат.",
        "portfolio_valid = False only when MaxDD on the full overlapping history breaches the mandate.",
    ),
    (
        "Сценарный стресс (DIAG_*) не делает портфель invalid.",
        "Scenario stress (DIAG_*) does not make the portfolio invalid.",
    ),
    ("Snapshot активов", "Asset snapshot"),
    ("Ошибка валидации конфигурации", "Configuration validation error"),
    ("Поля конфигурации, ожидающие ввода пользователя", "Configuration fields awaiting user input"),
    ("CSV в %s: asset_metrics", "CSV in %s: asset_metrics"),
    (
        "Финальные результаты в %s: portfolio_weights.yml",
        "Final results in %s: portfolio_weights.yml",
    ),
    ("Поля, ожидающие ввода пользователя", "Fields awaiting user input"),
    ("[OK] достигнута", "[OK] met"),
    ("[X] не достигнута", "[X] not met"),
    ("Целевая доходность:", "Target return:"),
    ("реализованная:", "realized:"),
    ("цель:", "target:"),
    ("реализовано:", "realized:"),
    ("Кеш сохранён в cache/", "Cache saved under cache/"),
    ("(дневной:", "(daily:"),
    ("месячный:", "monthly:"),
    ("включая кэш и tail", "including cash and tail"),
    ("без кэша", "ex cash"),
    ("топ-%d доноров риска", "top-%d risk contributors"),
    (
        "Нет {rr_path.name}. Сначала выполните оптимизацию и отчёт (run_optimization / run_report).",
        "Missing {rr_path.name}. Run optimization and report first (run_optimization / run_report).",
    ),
    ("остались:", "remaining:"),
    ("Stress (диаг.):", "Stress (diag.):"),
    ("сценарий:", "scenario:"),
    ('return f"Нет {p}", 404', 'return f"Not found: {p}", 404'),
    (
        "короткие, связные формулировки на русском",
        "short, connected English phrasing",
    ),
    (
        "статусы и сценарии  -  бытовым языком",
        "statuses and scenarios in plain language",
    ),
    ("якоря в commentary.txt (EN) -> видимый заголовок (RU, клиентский)", "anchors in commentary.txt (EN) -> visible PDF heading (English, client-facing)"),
    ("Заголовок в шапке PDF (слева), по имени итогового файла", "PDF header label (left), from output filename"),
    ('"Скв."', '"Skew."'),
    ('"Эксцесс"', '"Excess kurt."'),
    ("default_window_ru", "default_window_label"),
    ("10-летнем", "10-year"),
    ("5-летнем", "5-year"),
    ("3-летнем", "3-year"),
    (
        "Вторая строка титульного блока, как в эталоне: «итоги на N-летнем окне, по состоянию на ...».",
        "Subtitle line for the title block: results for the N-year window as of the analysis date.",
    ),
    (
        "Клиентский исполненческий тон: убрать внутренние коды, пути, «системные» обозначения.",
        "Client-facing tone: remove internal codes, paths, and system tokens.",
    ),
    (
        "Не сохраняет дословно исход  -  только безопасный для PDF смысл.",
        "Does not preserve source wording verbatim; keeps PDF-safe meaning only.",
    ),
    ("сильный обвал на рынке акций", "severe equity market decline"),
    ("стресс на рынке кредита", "credit market stress"),
    ("дата среза", "as-of date"),
    ("чувствительность к широкому рынку", "broad market sensitivity"),
    ("связь с рынком в целом", "overall market correlation"),
    ("оценка доходности с учётом чувствительности к рынку", "return per unit of market sensitivity (Treynor)"),
    ("расчёт по политике", "policy run"),
    ("в норме по проверке", "within the agreed risk profile"),
    (
        "Короткие формулировки для лицевой стороны  -  без внутренних кодов движка.",
        "Short labels for the client-facing side without internal engine codes.",
    ),
    (
        "Сырые причины-коды не печатаем; осмысленный текст  -  через санитайзер.",
        "Do not print raw reason codes; meaningful text goes through the sanitizer.",
    ),
    (
        "Текст для PDF: без внутренних ярлыков и сухой техники.",
        "PDF narrative text without internal labels or dry technical tokens.",
    ),
    ("H1: инсайт-заголовок", "H1: insight-style headline"),
    (
        "На горизонте **{wl}** (оценка **{ae}**) равные веса обычно сильнее ориентированы на **ожидаемую доходность**",
        "Over **{wl}** (as of **{ae}**), equal weights are usually more oriented to **expected return**",
    ),
    (
        "а **risk parity** сглаживает **вклад инструментов в общий риск**",
        "while **risk parity** smooths **each instrument's contribution to total risk**",
    ),
    ("Сравнение: equal-weight и risk parity", "Comparison: equal-weight and risk parity"),
    ("## Ключевой вывод", "## Key takeaway"),
    ("|  | Равные веса (EW) | Risk parity | Разница (EW - RP) |", "|  | Equal weights (EW) | Risk parity | Difference (EW - RP) |"),
    ("Кто сильнее всего влияет на риск (топ позиций)", "Largest risk contributors (top positions)"),
]

FILES = [
    REPO / "run_report.py",
    REPO / "src/snapshot.py",
    REPO / "results_dashboard/app.py",
    REPO / "src/pdf_reports.py",
    REPO / "src/io_export.py",
]


def main() -> None:
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"updated {path.relative_to(REPO)}")
        else:
            print(f"unchanged {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
