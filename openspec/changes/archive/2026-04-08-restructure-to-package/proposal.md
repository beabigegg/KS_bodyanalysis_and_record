## Why

專案目前由多個鬆散的頂層目錄（config, db, extractor, parsers, watcher, web）組成，不是正式的 Python package。Pipeline 和 Web 各有獨立的設定系統（`config/settings.py` vs `web/settings.py`），Web 透過 `sys.path` hack 存取上層模組，且沒有統一的啟動腳本。這導致部署流程碎片化（需要分別 cd 到不同目錄啟動）、設定重複維護、`requirements.txt` 不完整（缺少 FastAPI 等 Web 依賴），以及殘留的 `config.yaml` 含明文密碼在 git 歷史中。

專案即將遷移至 1panel 虛擬主機正式部署，需要一個乾淨、可 `pip install` 的 package 結構和單一入口。

## What Changes

- **BREAKING** 所有 Python import 路徑從頂層相對路徑改為 `ksbody.*` package 絕對路徑
- 合併 `config/settings.py` 和 `web/settings.py` 為單一 `ksbody/config.py`
- 移除 `web/deps.py` 中的 `sys.path.insert` hack 和 `db/init_db.py` 中的 `sys.path.append` hack
- 新增 `ksbody/__main__.py` 作為統一 CLI 入口（子命令：`pipeline`, `web`, `all`, `init-db`）
- 新增 `ksbody/manager.py` 實作 ProcessManager，支援多 process 管理、健康偵測、異常自動重啟
- 新增 `pyproject.toml` 取代 `requirements.txt`，完整列出所有依賴（含 FastAPI、uvicorn、pydantic）
- 前端目錄從 `web/frontend/` 搬入 `ksbody/web/frontend/`，隨 package 一起管理
- 移除殘留的 `config.yaml`，並清理 git 歷史中的明文密碼
- 新增 `scripts/deploy.sh` 整合前端 build + 後端安裝 + 服務啟動

## Capabilities

### New Capabilities
- `unified-config`: 單一設定來源，合併 pipeline 與 web 的所有環境變數解析，消除重複
- `process-manager`: 多 process 管理器，同時運行 pipeline 和 web 服務，含健康偵測（process alive + HTTP health check）和異常自動重啟（含重試上限與冷卻機制）
- `cli-entrypoint`: 統一 CLI 入口 `python -m ksbody`，支援 `pipeline | web | all | init-db` 子命令
- `deployment-scripts`: 1panel 部署腳本，整合前端 build、後端安裝、服務啟動

### Modified Capabilities
- `folder-watcher`: 模組路徑從 `watcher.*` 改為 `ksbody.watcher.*`，import 與設定取用方式變更
- `webui-backend`: 模組路徑從 `web/` 頂層改為 `ksbody.web.*`，移除 sys.path hack，改從統一 config 取得設定
- `env-config-pipeline`: 被 `unified-config` 取代，原有的 `config/settings.py` 將被移除

## Impact

- **所有 Python 檔案**：import 路徑全面改為 `ksbody.*` 前綴（約 30+ 檔案）
- **測試**：所有 test 檔案的 import 需同步更新
- **前端**：目錄位置變更，`vite.config` 可能需調整 proxy 路徑
- **部署**：從手動 `python main.py` / `cd web && python app.py` 改為 `pip install . && python -m ksbody all`
- **Git 歷史**：使用 `git filter-repo` 移除含密碼的 `config.yaml`，所有 commit hash 將改變
- **依賴管理**：從 `requirements.txt` 遷移至 `pyproject.toml`，新增 `oracledb` 為 optional dependency
