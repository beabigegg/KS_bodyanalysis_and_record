## Requirements

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

#### Scenario: Watch paths accessible from web process
- **WHEN** Web API 需要查詢監控路徑資訊
- **THEN** 系統 SHALL 透過 `ksbody.config.get_settings().watch_paths` 取得路徑列表，無需依賴 pipeline process 的內部狀態

### Requirement: Expose watcher runtime state
Watcher 模組 SHALL 暴露內部運行狀態供外部查詢。

#### Scenario: Query watcher running status
- **WHEN** 外部模組查詢 watcher 狀態
- **THEN** 系統 SHALL 回傳 watcher 是否正在運行、啟動時間、監控路徑列表

#### Scenario: Query watch path accessibility
- **WHEN** 外部模組查詢監控路徑狀態
- **THEN** 系統 SHALL 檢查每個監控路徑是否可存取（`Path.exists()`），回傳可用性與路徑下符合 recipe body 格式的檔案數量

### Requirement: FileStateStore supports clearing entries
`FileStateStore` SHALL 支援清除特定檔案的已處理標記。

#### Scenario: Clear single file state
- **WHEN** 呼叫 `FileStateStore.clear(file_path)` 指定特定檔案路徑
- **THEN** 系統 SHALL 移除該路徑在 state 中的紀錄，並持久化至磁碟

#### Scenario: Clear multiple file states
- **WHEN** 呼叫 `FileStateStore.clear_many(file_paths)` 指定多個路徑
- **THEN** 系統 SHALL 移除所有指定路徑的紀錄，並持久化至磁碟

#### Scenario: Clear non-existent entry
- **WHEN** 清除的路徑不存在於 state 中
- **THEN** 系統 SHALL 靜默忽略，不拋出例外
