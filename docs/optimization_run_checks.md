# Проверки при полном прогоне оптимизации

Документ описывает: **где и почему падает код**, **проблемы с подключением (сеть/API)**, **противоречия параметров** и **зависимости между шагами**.

---

## 1. Порядок выполнения и точки отказа

### 1.1 Загрузка конфигурации (`load_validated_config`)

| Что проверяется | Ошибка | Решение |
|-----------------|--------|---------|
| `config.yml` не найден | `FileNotFoundError` | Создать config.yml из config.yml.example |
| Обязательные поля пустые | `ConfigValidationError: Missing or empty required config fields: [...]` | Заполнить tickers, investor_currency и т.д. |
| Тикер из config не в blocks_universe | `ConfigValidationError: Ticker(s) not found in blocks_universe.yml: ...` | Добавить тикер в нужный блок в blocks_universe.yml или убрать из config tickers |
| Один тикер в двух блоках в blocks_universe | `ConfigValidationError: ticker 'X' appears in both 'Y' and 'Z'` | Оставить тикер только в одном блоке |
| `client_profile` задан, но профиля нет в client_profiles.yml | Профиль не применится, rc_block_targets могут остаться пустыми | Использовать id из списка: ultra_conservative, conservative, balanced, **growth**, aggressive (регистр не важен — приводится к lower) |
| `investor_currency` не USD и не EUR, а cash_proxy / risk_free не заданы | `ConfigValidationError: No default for investor_currency=JPY. Set cash_proxy_ticker and risk_free_source...` | Явно задать в config.yml `cash_proxy_ticker` и `risk_free_source` для JPY/CHF и др. |

### 1.2 Профиль и rc_block_targets (в run_optimization.py)

| Условие | Ошибка | Решение |
|---------|--------|---------|
| rc_block_targets пустые после применения профиля | `SystemExit(1): rc_block_targets не заданы. Укажите client_profile (например Growth)...` | Задать в config `client_profile: growth` (или другой из client_profiles.yml) или вручную заполнить rc_block_targets |
| В блоках Growth/Duration/Inflation нет ни одного тикера | `SystemExit(1): В конфиге нет тикеров в блоках Growth, Duration или Inflation` | Добавить хотя бы один тикер в каждый из блоков в blocks_universe и убедиться, что эти тикеры есть в config tickers |

### 1.3 Загрузка данных (`load_monthly_data_shared`)

Здесь происходят **сетевые запросы**. При отсутствии сети или блокировке API скрипт падает или зависает.

| Источник | Где используется | Возможная ошибка / поведение |
|----------|------------------|------------------------------|
| **Yahoo Finance (yfinance)** | Цены по всем тикерам (активы, бенчмарк, cash proxy, FX) | Таймаут, пустой DataFrame по тикеру (тикер пропускается в daily), при полном сбое — необработанное исключение из yf.download |
| **FRED** (pandas_datareader) | risk_free_source вида `FRED:DTB3` | `ImportError` если нет pandas-datareader; при недоступности API — исключение из get_data_fred; пустой ряд → rf_monthly пустой |
| **ECB €STR** (api.estr.dev) | risk_free_source вида `ECB:€STR` для EUR | `urllib.error.URLError` / timeout при отсутствии сети или блокировке; без VPN/туннеля запрос к api.estr.dev может не проходить в части сетей |

**Важно:** в коде нет явного «туннеля» или прокси; если у вас корпоративный firewall или страна блокирует доступ к Yahoo/FRED/estr.dev, нужны:

- рабочая сеть или VPN;
- либо явная настройка прокси в окружении (например `HTTP_PROXY`/`HTTPS_PROXY`), если используемые библиотеки их подхватывают.

### 1.4 Risk-budget оптимизация (`run_risk_budget_optimization`)

| Ситуация | Результат | Что делать |
|----------|------------|------------|
| Оптимизатор не сошёлся по ограничениям | Возвращается fallback (равные веса по блокам), status содержит "OK (fallback)" | Проверить rc_block_targets, ограничения по весам (min/max_single_security_weight_pct), rc_asset_cap_pct; при необходимости ослабить ограничения или добавить активы |
| Нет допустимого решения | `weights_risk` пустой, status — сообщение об ошибке | `SystemExit(1): Оптимизация не удалась: <status>` — ослабить ограничения или изменить блоки/тикеры |

### 1.5 ProLiquidity и Alpha Shift

| Условие | Ошибка | Решение |
|---------|--------|---------|
| cash_policy = prohibited, текущая волатильность > target_vol, Alpha Shift не смог снизить vol до target | `ProLiquidity: TargetVol cannot be achieved with cash_policy='prohibited' given the current universe and constraints.` → SystemExit(1) | Разрешить кэш (cash_policy: allowed_for_scaling) или ослабить target_vol / добавить низковолатильные активы |
| В портфеле нет ни VOO/VT/VTI, ни Duration/Inflation | `No recipient (VOO/VT/VTI or Duration/Inflation) in portfolio for alpha shift` | Добавить в универсум один из VOO, VT, VTI или активы Duration/Inflation |

---

## 2. Сеть и «не туннель»

- **Туннель (VPN)** в коде нигде не настраивается. Все запросы идут так, как разрешает среда (ОС/сеть).
- Места, где код выходит в интернет:
  - **src/data_yf.py** — yfinance → Yahoo Finance;
  - **src/data_fred.py** — pandas_datareader → FRED (нужен pandas-datareader);
  - **src/data_ecb.py** — urllib.request → https://api.estr.dev (ECB €STR).
- Если что-то «не работает» при прогоне:
  1. Проверить доступность в браузере или curl: Yahoo, FRED, api.estr.dev.
  2. При блокировках — использовать VPN или прокси (переменные окружения прокси, если библиотеки их поддерживают).
  3. Для FRED при лимитах API может понадобиться FRED_API_KEY в окружении.

---

## 3. Противоречия и несоответствия параметров

| Параметр A | Параметр B | Конфликт | Рекомендация |
|------------|------------|----------|--------------|
| **investor_currency: EUR** (или JPY/CHF) | **risk_free_source** не задан | Для не‑USD дефолты есть только у USD и EUR. JPY/CHF без явных cash_proxy и risk_free → ошибка валидации | Явно задать risk_free_source и cash_proxy_ticker для не‑USD |
| **cash_policy: prohibited** | **target_vol_annual** низкая, а активы высоковолатильные | TargetVol недостижима без кэша → ошибка ProLiquidity/Alpha Shift | Либо allowed_for_scaling, либо выше target_vol / больше облигаций |
| **rc_block_targets** (сумма ≠ 1) | Спека: сумма = 1 | В коде нормализация есть (normalize_rc_block_targets), но лучше изначально задавать сумму 1 | Задавать сумму 1 или положиться на нормализацию |
| **client_profile: Growth** в config | В client_profiles.yml ключ **growth** (lowercase) | Профиль ищется по pid = profile_id.strip().lower() — то есть "Growth" → "growth". Имена в yml должны быть в lower case | Ок, если в yml именно growth, conservative и т.д. |
| **weights** в config.yml | Политика: «веса только из оптимизации» | Если в config есть weights, load_validated_config подхватит их; run_optimization перезаписывает веса оптимизацией и при --write-config пишет в config | Сначала запускать оптимизацию, отчёт — после; не редактировать веса вручную по политике |
| **tickers** в config | Состав блоков в **blocks_universe.yml** | Каждый тикер из config должен быть ровно в одном блоке в blocks_universe | Синхронизировать tickers и blocks_universe |

---

## 4. Зависимости между скриптами

- **run_optimization.py**  
  Читает config.yml (и при наличии — client_profile из файла), blocks_universe.yml, config/client_profiles.yml; качает данные (Yahoo, FRED/ECB); пишет **portfolio_weights.yml** (и при --write-config — weights в config.yml).

- **run_report.py**  
  Читает config.yml и при отсутствии weights — **portfolio_weights.yml**. Для отчёта нужны веса: либо из оптимизации (portfolio_weights.yml), либо из config.

**Порядок:** сначала `python run_optimization.py` (при необходимости с `--no-cache`), затем `python run_report.py`. Иначе отчёт будет с пустыми или устаревшими весами.

---

## 5. Краткий чеклист перед полным прогоном

1. **config.yml**: все обязательные поля заполнены; tickers совпадают с blocks_universe.yml; при не‑USD заданы cash_proxy_ticker и risk_free_source.
2. **blocks_universe.yml**: каждый тикер из config ровно в одном блоке; есть тикеры в Growth, Duration, Inflation.
3. **client_profile**: указан один из ultra_conservative, conservative, balanced, growth, aggressive (или заданы rc_block_targets вручную).
4. **Сеть**: доступ к Yahoo Finance, FRED (и при EUR — к api.estr.dev); при блокировках — VPN/прокси.
5. **Зависимости**: установлен pandas-datareader (для FRED).
6. После оптимизации: проверить, что создался portfolio_weights.yml; затем запускать run_report.py.

Если после этого что-то всё ещё «не работает», смотреть текст ошибки в консоли и сопоставлять с таблицами выше (конфиг, профиль, данные, оптимизация, ProLiquidity).
