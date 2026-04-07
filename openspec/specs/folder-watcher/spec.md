## ADDED Requirements

### Requirement: Watch network folder for recipe body changes
系統 SHALL 監聽可配置的網路資料夾路徑，遞迴偵測所有子目錄中 recipe body 檔案的新增或修改事件。

#### Scenario: New recipe body file detected
- **WHEN** 一個新的 recipe body 檔案出現在 `{監聽根目錄}/{機型}_EAP/{machine_id}/` 路徑下
- **THEN** 系統觸發解析流程，傳入完整檔案路徑

#### Scenario: Existing recipe body file modified
- **WHEN** 一個已存在的 recipe body 檔案被覆蓋更新（mtime 改變）
- **THEN** 系統觸發解析流程，建立新的解析記錄（不覆蓋舊記錄）

#### Scenario: Debounce rapid file events
- **WHEN** 同一檔案在短時間內觸發多次事件（如 create + modify）
- **THEN** 系統 SHALL 等待檔案 mtime 穩定後（至少 5 秒無變化）才觸發解析，避免重複或解析不完整的檔案

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

### Requirement: Periodic full scan as compensation
系統 SHALL 定期執行全量掃描，比對已入庫記錄與磁碟檔案的 mtime，補償 watchdog 可能錯過的事件。

#### Scenario: Full scan detects missed file
- **WHEN** 定期掃描發現某檔案的 mtime 晚於該檔案最後一次入庫的時間
- **THEN** 系統觸發該檔案的解析流程

### Requirement: File path pattern filtering
系統 SHALL 僅處理符合 recipe body 檔名規則的檔案，忽略其他檔案。

#### Scenario: Valid recipe body file
- **WHEN** 偵測到檔名符合 `L_{機型}@{product_type}@{bop}@{wafer_pn}_{version}` 格式的檔案
- **THEN** 系統接受並觸發解析

#### Scenario: Non-recipe file ignored
- **WHEN** 偵測到不符合命名格式的檔案（如 .tmp、.log 或其他）
- **THEN** 系統 SHALL 忽略該檔案，不觸發解析
