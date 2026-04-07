## Why

公司 AI 賦能部發布了「App 開發設計規範 v1.3」，所有需部署的應用必須通過佈署前檢查清單才能上線。目前專案在多項規範上不合規：pipeline 服務使用 config.yaml 硬編碼敏感資訊、根目錄 requirements.txt 未鎖定版本、缺少必要文件（README.md / SDD.md / TDD.md / PRD.md）、.gitignore 不完整、存在應清理的開發殘留。現在需要一次性整頓，使專案達到 PRD-ready 狀態。

## What Changes

### 組態與機敏資訊
- **BREAKING** — Pipeline 服務從 `config.yaml` 遷移至 `.env` 環境變數（與 web 統一），消除硬編碼的 MySQL 密碼與 SMB 帳號
- 建立統一的根目錄 `.env.example`，涵蓋 pipeline + web 所有設定
- 移除或重構 `config/settings.py` 以讀取環境變數而非 YAML
- 移除 `config.yaml.example`，改由 `.env.example` 取代

### 依賴管理
- 根目錄 `requirements.txt` 版本鎖定（`>=` → `==`），並加註套件用途
- 合併或明確區分根目錄與 `web/` 的 requirements.txt

### 專案清理
- 移除 `legacy/` 目錄（已棄用的舊程式）
- 移除 `samples/` 目錄（測試用範例資料，不應進 repo）
- 移除 `web/recipe.db`（SQLite 資料庫檔案不應追蹤）
- 清理追蹤中的 `__pycache__/`、`.pytest_cache/` 等快取目錄

### .gitignore 補強
- 新增 `build/`、`dist/`（非 web 路徑）、`*.db`、`*.sqlite3`、`nul` 等遺漏項目

### 必要文件補齊
- 建立 `README.md`（專案介紹、安裝、啟動、環境變數說明）
- PRD / SDD / TDD 由 OpenSpec 開發紀錄涵蓋，不另建

### Logging 合規確認
- 掃描全專案確認無 `print` 用於正式 log、無敏感資訊外洩至 log

## Capabilities

### New Capabilities
- `env-config-pipeline`: Pipeline 服務環境變數化組態（取代 config.yaml）
- `project-docs`: PRD-ready 必要文件（README / SDD / TDD / PRD）

### Modified Capabilities
- `folder-watcher`: 啟動設定來源從 config.yaml 改為 .env 環境變數
- `database-storage`: 連線設定從 YAML 改為環境變數

## Impact

- **config/settings.py** — 需重寫為 .env 讀取，所有引用此模組的程式碼受影響（main.py、pipeline.py、db/repository.py）
- **啟動流程** — `python main.py --config config.yaml` 將改為 `python main.py`（從 .env 讀取）
- **CI/部署** — 需更新部署腳本，準備 `.env` 而非 `config.yaml`
- **Git 歷史** — 移除 legacy/、samples/、web/recipe.db 等檔案（不可逆但已無用途）
- **相依套件** — 新增 `python-dotenv` 至根目錄 requirements.txt
