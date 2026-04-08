## ADDED Requirements

### Requirement: Single settings source for all services
系統 SHALL 提供單一 `ksbody.config` 模組作為 pipeline 與 web 共用的設定來源，取代原本分離的 `config/settings.py` 和 `web/settings.py`。

#### Scenario: Load all settings from one module
- **WHEN** 任何模組呼叫 `get_settings()`
- **THEN** 系統回傳包含 MySQL、debounce、watch paths、web server、Oracle 等所有設定的 `Settings` 物件

#### Scenario: Settings singleton via lru_cache
- **WHEN** 多個模組在同一 process 中呼叫 `get_settings()`
- **THEN** 系統 SHALL 回傳相同的 `Settings` 實例（透過 `functools.lru_cache`）

#### Scenario: Single load_dotenv call
- **WHEN** `get_settings()` 首次被呼叫
- **THEN** 系統 SHALL 僅執行一次 `load_dotenv()`，從專案根目錄的 `.env` 載入環境變數

### Requirement: Merged MySQL configuration
系統 SHALL 統一 MySQL 連線設定，pipeline 和 web 共用同一個 `MySQLConfig` dataclass。

#### Scenario: Pipeline uses unified MySQL config
- **WHEN** pipeline 建立 `RecipeRepository`
- **THEN** 系統從 `get_settings().mysql` 取得連線資訊

#### Scenario: Web uses unified MySQL config
- **WHEN** web 的 `deps.py` 建立 SQLAlchemy engine
- **THEN** 系統從 `get_settings().mysql.sqlalchemy_url()` 取得連線字串

### Requirement: Optional Oracle configuration
系統 SHALL 支援 Oracle 連線為可選設定，未配置時不影響啟動。

#### Scenario: Oracle env vars present
- **WHEN** `ORACLE_DSN`、`ORACLE_USER`、`ORACLE_PASSWORD` 皆已設定
- **THEN** `get_settings().oracle` 回傳 `OracleConfig` 物件

#### Scenario: Oracle env vars absent
- **WHEN** Oracle 相關環境變數未設定
- **THEN** `get_settings().oracle` 回傳 `None`，web 的 yield correlation 功能不啟用

### Requirement: Graceful defaults for mode-specific settings
系統 SHALL 對只有特定服務需要的設定提供合理預設值，使單獨啟動 pipeline 或 web 時不需要配置對方的必要變數。

#### Scenario: Run web without WATCH_PATHS
- **WHEN** 僅啟動 web 服務且 `WATCH_PATHS` 未設定
- **THEN** `get_settings().watch_paths` 回傳空 list，不拋出錯誤

#### Scenario: Run pipeline without APP_HOST
- **WHEN** 僅啟動 pipeline 且 `APP_HOST` 未設定
- **THEN** `get_settings().app_host` 使用預設值 `0.0.0.0`
