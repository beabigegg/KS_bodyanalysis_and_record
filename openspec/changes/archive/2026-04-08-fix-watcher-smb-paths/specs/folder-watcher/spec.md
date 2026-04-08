## MODIFIED Requirements

### Requirement: Configurable watch paths
系統 SHALL 從環境變數讀取監聽根目錄路徑，支援多個根目錄配置。

#### Scenario: Load watch paths from .env
- **WHEN** 服務啟動
- **THEN** 系統從 `ksbody.config.get_settings().watch_paths` 取得路徑列表，對每個路徑啟動監聽

#### Scenario: Watch path unavailable
- **WHEN** 配置的網路路徑無法存取
- **THEN** 系統 SHALL 記錄 warning 日誌並跳過該路徑；若**所有**路徑均不可用則拋出 `RuntimeError`
- **NOTE** 不實作執行期重試。部署層（`deploy.sh`）負責確保 SMB 掛載在 watcher 啟動前就緒，是此行為的前提。

#### Scenario: Recipe traceability SMB path included
- **WHEN** `WATCH_PATHS` 指向 SMB 掛載後的本地路徑（如 `/mnt/eap_recipe/WBK_ConnX Elite`）
- **THEN** 系統 SHALL 對該路徑啟動 PollingObserver 遞迴監聽，自動涵蓋所有機台子資料夾中的 recipe body 檔案

#### Scenario: Import path changed to ksbody.watcher
- **WHEN** 其他模組需要引用 watcher 功能
- **THEN** 系統 SHALL 使用 `ksbody.watcher.*` import 路徑（取代原本的 `watcher.*`）
