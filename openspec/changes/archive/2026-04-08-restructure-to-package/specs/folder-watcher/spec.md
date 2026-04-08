## MODIFIED Requirements

### Requirement: Configurable watch paths
系統 SHALL 從環境變數讀取監聽根目錄路徑，支援多個根目錄配置。

#### Scenario: Load watch paths from .env
- **WHEN** 服務啟動
- **THEN** 系統從 `ksbody.config.get_settings().watch_paths` 取得路徑列表，對每個路徑啟動監聽

#### Scenario: Watch path unavailable
- **WHEN** 配置的網路路徑無法存取
- **THEN** 系統 SHALL 記錄錯誤日誌並持續重試連接，不中斷其他路徑的監聯

#### Scenario: Recipe traceability SMB path included
- **WHEN** `WATCH_PATHS` 包含 recipe 追溯 SMB 共享路徑
- **THEN** 系統 SHALL 對該路徑啟動與其他路徑相同的 PollingObserver 監聽和 FullScanner 定期掃描

#### Scenario: Import path changed to ksbody.watcher
- **WHEN** 其他模組需要引用 watcher 功能
- **THEN** 系統 SHALL 使用 `ksbody.watcher.*` import 路徑（取代原本的 `watcher.*`）
