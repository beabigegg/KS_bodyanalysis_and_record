## 1. Package 結構調整

- [x] 1.1 建立 `ksbody/` 目錄與 `__init__.py`
- [x] 1.2 建立 `pyproject.toml`，定義 project metadata、dependencies、optional-dependencies（oracle）、console script entrypoint
- [x] 1.3 刪除 `requirements.txt`

## 2. 統一設定模組

- [x] 2.1 建立 `ksbody/config.py`，合併 `config/settings.py` 和 `web/settings.py` 為單一 `Settings` dataclass，含 `MySQLConfig`、`DebounceConfig`、`OracleConfig`，使用 `lru_cache` 提供 `get_settings()`
- [x] 2.2 實作 graceful defaults：`watch_paths` 在未設定時回傳空 list，web 設定提供合理預設值
- [x] 2.3 更新 `.env.example`，加入所有變數的統一註解

## 3. 搬移模組與 import 路徑更新

- [x] 3.1 搬移 `db/` → `ksbody/db/`，更新所有 import 為 `ksbody.db.*`
- [x] 3.2 搬移 `parsers/` → `ksbody/pipeline/parsers/`，更新內部 import 為 `ksbody.pipeline.parsers.*`
- [x] 3.3 搬移 `extractor/` → `ksbody/pipeline/extractor/`，更新 import 為 `ksbody.pipeline.extractor.*`
- [x] 3.4 搬移 `pipeline.py` → `ksbody/pipeline/__init__.py`，更新其 import（db、extractor、parsers）
- [x] 3.5 搬移 `watcher/` → `ksbody/watcher/`，更新 import（`config.settings` → `ksbody.config`，內部 import 加 `ksbody.` 前綴）
- [x] 3.6 搬移 `web/` → `ksbody/web/`（含 frontend/），更新所有 import 為 `ksbody.web.*`
- [x] 3.7 移除 `ksbody/web/deps.py` 中的 `sys.path.insert` hack，改用 `from ksbody.db.schema import metadata`
- [x] 3.8 移除 `web/settings.py`（功能已併入 `ksbody/config.py`）
- [x] 3.9 移除舊的 `config/` 目錄（功能已併入 `ksbody/config.py`）
- [x] 3.10 搬移 `main.py` 的 pipeline 啟動邏輯到 `ksbody/pipeline/runner.py`

## 4. CLI 入口

- [x] 4.1 建立 `ksbody/__main__.py`，使用 `argparse` 實作子命令：`pipeline`、`web`、`all`、`init-db`
- [x] 4.2 `pipeline` 子命令：呼叫 `ksbody.pipeline.runner` 啟動 watcher 服務，支援 `--process-file` 選項
- [x] 4.3 `web` 子命令：呼叫 `uvicorn` 啟動 FastAPI 應用
- [x] 4.4 `all` 子命令：呼叫 `ProcessManager` 同時管理 pipeline 和 web
- [x] 4.5 `init-db` 子命令：建立 DB schema 後退出
- [x] 4.6 刪除舊的 `main.py`

## 5. ProcessManager

- [x] 5.1 建立 `ksbody/manager.py`，實作 `ProcessManager` class
- [x] 5.2 實作 `_run_pipeline()` 和 `_run_web()` 作為子 process target function
- [x] 5.3 實作健康檢查迴圈：每 10 秒 `is_alive()` 檢查，每 30 秒 HTTP `/api/health` 檢查（含 15 秒 grace period）
- [x] 5.4 實作自動重啟邏輯：指數退避（base=2s, max=60s）、max_restarts=5、穩定運行 120 秒後重置計數器
- [x] 5.5 實作信號處理：SIGTERM/SIGINT 優雅關閉子 process

## 6. 測試與驗證

- [x] 6.1 更新 `tests/` 下所有測試檔的 import 路徑為 `ksbody.*`
- [x] 6.2 更新 `web/tests/` → `ksbody/web/tests/` 的 import 路徑
- [x] 6.3 驗證 `python -m ksbody pipeline --process-file <test-file>` 可正常執行
- [x] 6.4 驗證 `python -m ksbody web` 可正常啟動並回應 `/api/health`
- [x] 6.5 驗證 `python -m ksbody all` 可同時啟動兩個服務

## 7. 部署與文件

- [x] 7.1 建立 `scripts/deploy.sh`：virtualenv 建立、pip install、前端 build、服務啟動
- [x] 7.2 更新 `.gitignore`（加入 `*.egg-info/`、`dist/`、`build/`）
- [x] 7.3 刪除殘留的 `config.yaml`
- [x] 7.4 使用 `git filter-repo --path config.yaml --invert-paths` 清理 git 歷史中的明文密碼
- [x] 7.5 更新 `README.md`，記錄新的安裝與啟動方式


