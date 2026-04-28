# Проверки при полном прогоне оптимизации

Документ описывает: **где и почему падает код**, **проблемы с подключением (сеть/API)**, **противоречия параметров** и **зависимости между шагами**. Модель портфеля — **без блочного risk budget** и без `blocks_universe.yml` (см. `docs/portfolio_construction_policy.md`).

---

## 1. Порядок выполнения и точки отказа

### 1.1 Загрузка конфигурации (`load_validated_config`)

| Что проверяется | Ошибка | Решение |
|-----------------|--------|---------|
| `config.yml` не найден | `FileNotFoundError` | Создать `config.yml` из `config.yml.example` |
| Обязательные поля пустые | `ConfigValidationError: Missing or empty required config fields: [...]` | Заполнить `tickers`, `investor_currency` и остальное по схеме |
| Некорректные числовые/процентные поля | `ConfigValidationError` с указанием поля | Привести значения к формату, ожидаемому `validate_config` |
| `client_profile` задан, но профиля нет в `client_profiles.yml` | Профиль не подставится; цели из профиля не заполнятся | Использовать id из файла: `ultra_conservative`, `conservative`, `balanced`, `growth`, `aggressive` (регистр приводится к lower) |
| `investor_currency` не USD/EUR и не заданы `cash_proxy_ticker` / `risk_free_source` | `ConfigValidationError` с текстом про явную настройку | Задать в `config.yml` кэш и безрисковую ставку для валюты инвестора |

### 1.2 Профиль клиента (`client_profiles.yml`)

Профиль задаёт (в числе прочего) диапазоны или значения для **целевой волатильности**, **MaxDD**, **целевой номинальной доходности** — см. актуальный YAML. **Блочные цели RC (Growth/Duration/Inflation) в конфиге не используются.**

### 1.3 Загрузка данных (`load_monthly_data_shared`)

Здесь происходят **сетевые запросы**. При отсутствии сети или блокировке API скрипт падает или долго ждёт.

| Источник | Где используется | Возможная ошибка / поведение |
|----------|------------------|------------------------------|
| **Yahoo Finance (yfinance)** | Цены по всем тикерам (активы, бенчмарк, cash proxy, FX) | Таймаут, пустой ряд по тикеру, при полном сбое — исключение из `yf.download` |
| **FRED** (pandas_datareader) | `risk_free_source` вида `FRED:DTB3` | `ImportError`, если нет pandas-datareader; при недоступности API — исключение; пустой ряд → пустой `rf_monthly` |
| **ECB €STR** (api.estr.dev) | `risk_free_source` вида `ECB:€STR` для EUR | `URLError` / timeout; в части сетей без доступа к api.estr.dev запрос не проходит |

**Важно:** явного «туннеля» в коде нет; при firewall / блокировках регионов нужны VPN или прокси (`HTTP_PROXY` / `HTTPS_PROXY`), если библиотеки их подхватывают.

### 1.4 Оптимизация (`run_max_return_optimization` в `run_optimization.py`)

Историческое имя функции; по смыслу это **одностадийная** максимизация ожидаемой доходности с штрафами за отклонение от целевой vol/return и ограничениями по **весу** (см. `docs/portfolio_construction_policy.md`, `docs/docs/feasibility_constraints_spec.md`). **RC_vol** не входит в ограничения оптимизатора.

| Ситуация | Результат | Что делать |
|----------|------------|------------|
| Оптимизатор не сошёлся / ошибка данных | См. лог и `run_result.json` (**FAIL_DATA** и т.д.) | Проверить min/max веса по бумагам, состав `tickers`, данные, ковариацию |
| Fallback оптимизатора (ветка **OK_FALLBACK**) | В `run_result.json`: **OK_FALLBACK** в `optimization_status` | Смотреть сообщения оптимизатора; поле `rc_breaches` зарезервировано и **пустое** |

### 1.5 ProLiquidity и alpha-shift

| Условие | Ошибка | Решение |
|---------|--------|---------|
| `cash_policy = prohibited`, волатильность выше целевой, alpha-shift не доводит vol до target | Сообщение ProLiquidity / `SystemExit` | Разрешить кэш (`allowed_for_scaling`), поднять `target_vol_annual`, добавить низковолатильные активы |
| Пустой набор доноров для alpha-shift | Текст вида **Donor set empty for alpha shift** | Убедиться, что в риск-портфеле есть имена с положительным весом и ненулевым RC; при необходимости увеличить `N_rc` |

---

## 2. Сеть и «не туннель»

- **VPN** в коде не настраивается.
- Исходящие запросы: **src/data_yf.py** (Yahoo), **src/data_fred.py** (FRED), **src/data_ecb.py** (€STR).
- При проблемах: проверить доступность в браузере/curl; VPN/прокси; для FRED при лимитах — `FRED_API_KEY`.

---

## 3. Противоречия и несоответствия параметров

| Параметр A | Параметр B | Конфликт | Рекомендация |
|------------|------------|----------|--------------|
| **investor_currency: JPY/CHF** | Не заданы `cash_proxy_ticker` / `risk_free_source` | Ошибка валидации | Явно задать кэш и безрисковую ставку |
| **cash_policy: prohibited** | Низкая **target_vol_annual** и высоковолатильный универсум | Target vol недостижима | Разрешить кэш или скорректировать цели/универсум |
| **client_profile: Growth** в config | В YAML ключ **`growth`** (lowercase) | Нормально: id профиля нормализуется к lower | В `client_profiles.yml` ключи профилей в lower case |
| **weights** в config | Политика «веса из оптимизации» | Ручные веса могут быть перезаписаны прогоном | Сначала оптимизация, затем отчёт |

---

## 4. Зависимости между скриптами

- **run_optimization.py** — читает `config.yml`, `config/client_profiles.yml`, качает данные; пишет **`portfolio_weights.yml`**, **`run_result.json`**, стресс и снимки в `output_dir_final`.
- **run_report.py** — читает `config.yml` и при отсутствии весов в конфиге — **`portfolio_weights.yml`** из `output_dir_final`.

**Порядок:** сначала `python run_optimization.py`, затем `python run_report.py` (при необходимости `--no-cache`).

---

## 5. Актуальные акценты политики

1. **Нет блочного RB:** целевые доли риска по смысловым сегментам Growth/Duration/Inflation **не задаются** и **не оптимизируются**.
2. **RC_vol / Top1 / Top3 в стрессе:** только **диагностика** в отчётах и JSON; не блокируют запись весов и не задают пороги в конфиге.
3. **Мандат MaxDD** на полной пересекающейся истории — основной **жёсткий** барьер на запись весов наряду с **FAIL_DATA**; стресс — **DIAG_*** (не блокирует веса при успешном мандате).
4. **backtest_mode:** `dynamic_nan_safe` (по умолчанию) vs `simple` — см. `docs/data_policy_nan_young_etfs.md`.
5. **Dual-horizon robustness:** при включённой политике — сравнение 10Y vs 5Y весов и per-asset RC; флаги в `robustness_report.json` (см. `src/robustness.py`).

---

## 6. Чеклист перед полным прогоном

1. **config.yml:** обязательные поля; для не‑USD — cash и rf явно.
2. **client_profile** при необходимости — существующий id в `client_profiles.yml`.
3. **Сеть:** Yahoo, FRED (и при EUR — api.estr.dev).
4. **Зависимости:** `pandas-datareader` для FRED.
5. После оптимизации: **`portfolio_weights.yml`**, **`run_result.json`**; затем **`run_report.py`**.

Если что-то падает — текст в консоли и таблицы выше; детали статусов — **`docs/production_workflow.md`**.
