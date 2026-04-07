## MODIFIED Requirements

### Requirement: Configurable watch paths
系統 SHALL 從 YAML 配置檔讀取監聽根目錄路徑，支援多個根目錄配置。

#### Scenario: Load watch paths from config
- **WHEN** 服務啟動
- **THEN** 系統從 `config.yaml` 讀取 `watch_paths` 列表，對每個路徑啟動監聽

#### Scenario: Watch path unavailable
- **WHEN** 配置的網路路徑無法存取
- **THEN** 系統 SHALL 記錄錯誤日誌並持續重試連接，不中斷其他路徑的監聽

#### Scenario: Recipe traceability SMB path included
- **WHEN** `config.yaml` 的 `watch_paths` 包含 recipe 追溯 SMB 共享路徑 `\\10.1.1.43\eap_recipe_tracebility\WBK_ConnX Elite`
- **THEN** 系統 SHALL 對該路徑啟動與其他路徑相同的 PollingObserver 監聽和 FullScanner 定期掃描
