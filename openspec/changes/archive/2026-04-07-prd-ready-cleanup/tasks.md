## 1. Pipeline 組態遷移（config.yaml → .env）

- [x] 1.1 重寫 `config/settings.py`：移除 yaml import，改用 `python-dotenv` + `os.getenv()` 讀取所有設定（MYSQL_*、WATCH_PATHS、DEBOUNCE_*、SCAN_INTERVAL、LOG_FILE、STATE_FILE）
- [x] 1.2 更新 `main.py`：移除 `--config` 必要參數（改為可選或移除），呼叫新的 `load_settings()` 不帶參數
- [x] 1.3 確認 `db/repository.py` 的連線建立與新 settings 介面相容
- [x] 1.4 建立根目錄統一 `.env.example`（合併 pipeline + web 全部變數，附用途註解）
- [x] 1.5 移除 `web/.env.example`（已統一至根目錄）
- [x] 1.6 移除 `config.yaml.example`

## 2. 依賴管理

- [x] 2.1 更新根目錄 `requirements.txt`：鎖定版本（`==`）、新增 `python-dotenv`、移除 `pyyaml`、每行加 `#` 用途註解
- [x] 2.2 確認 `web/requirements.txt` 版本鎖定格式正確（已合規，僅需確認）

## 3. 專案清理

- [x] 3.1 `git rm -r legacy/` — 移除已棄用程式碼
- [x] 3.2 `git rm -r samples/` — 移除測試範例資料
- [x] 3.3 `git rm web/recipe.db` — 移除 SQLite 資料庫檔案
- [x] 3.4 清理追蹤中的 `__pycache__/`、`.pytest_cache/` 快取目錄（若有被追蹤）

## 4. .gitignore 補強

- [x] 4.1 更新 `.gitignore`：新增 `build/`、`dist/`、`*.db`、`*.sqlite3`、`nul`、`.env/`（虛擬環境）等遺漏項目

## 5. 必要文件建立

- [x] 5.1 建立 `README.md`：專案介紹、架構簡述、安裝方式（pip install）、環境變數說明（指向 .env.example）、pipeline 啟動指令、web 啟動指令、佈署說明
（PRD / SDD / TDD 由 OpenSpec 開發紀錄涵蓋，不另建）

## 6. Logging 合規掃描

- [x] 6.1 掃描全專案確認無 `print()` 用於正式 log 輸出
- [x] 6.2 確認 log 中無敏感資訊（密碼、token 等）外洩

## 7. 驗證

- [x] 7.1 確認 `python main.py --help` 正常執行
- [x] 7.2 確認 `cd web && python app.py` 正常啟動
- [x] 7.3 對照規範佈署前檢查清單 8 大類逐項確認通過
