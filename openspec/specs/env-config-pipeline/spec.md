## ADDED Requirements

### Requirement: Pipeline settings from environment variables
Pipeline 服務 SHALL 從環境變數（透過 `.env` 檔案載入）讀取所有設定，取代 config.yaml。

#### Scenario: Load MySQL connection from .env
- **WHEN** pipeline 服務啟動
- **THEN** 系統從 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`、`MYSQL_CHARSET` 環境變數建立資料庫連線

#### Scenario: Load watch paths from .env
- **WHEN** pipeline 服務啟動
- **THEN** 系統從 `WATCH_PATHS` 環境變數（逗號分隔）讀取監聽路徑列表

#### Scenario: Load debounce settings from .env
- **WHEN** pipeline 服務啟動
- **THEN** 系統從 `DEBOUNCE_SETTLE_SECONDS`、`DEBOUNCE_POLL_SECONDS`、`DEBOUNCE_STABLE_CHECKS` 環境變數讀取防抖設定，未設定時使用預設值（5、1、2）

#### Scenario: Load scan and log settings from .env
- **WHEN** pipeline 服務啟動
- **THEN** 系統從 `SCAN_INTERVAL`（預設 300）、`LOG_FILE`（預設 logs/recipe_import.log）、`STATE_FILE`（預設 state/processed_files.json）環境變數讀取設定

#### Scenario: Missing required variable
- **WHEN** 必要的環境變數（如 `MYSQL_HOST`）未設定且無預設值
- **THEN** 系統 SHALL 拋出明確的錯誤訊息，指出缺少的變數名稱

### Requirement: Unified .env.example at project root
專案根目錄 SHALL 提供單一 `.env.example`，涵蓋 pipeline 和 web 全部環境變數。

#### Scenario: .env.example contains all variables
- **WHEN** 開發者查閱 `.env.example`
- **THEN** 檔案包含所有 pipeline 變數（WATCH_PATHS、MYSQL_*、DEBOUNCE_*、SCAN_INTERVAL、LOG_FILE、STATE_FILE）和所有 web 變數（APP_*、ORACLE_*、RECIPE_TRACE_SMB_*），每個變數附有用途註解

#### Scenario: No sensitive values in .env.example
- **WHEN** 檢查 `.env.example` 內容
- **THEN** 所有密碼欄位 SHALL 使用 placeholder（如 `change-me`），不得包含真實密碼

### Requirement: Remove config.yaml dependency
專案 SHALL 移除對 config.yaml 的依賴。

#### Scenario: config.yaml.example removed
- **WHEN** 專案完成遷移
- **THEN** `config.yaml.example` 檔案從 repo 中移除，`config/settings.py` 不再 import yaml

#### Scenario: pyyaml removed from pipeline requirements
- **WHEN** 檢查根目錄 `requirements.txt`
- **THEN** `pyyaml` 不再列於依賴中，`python-dotenv` 已新增
