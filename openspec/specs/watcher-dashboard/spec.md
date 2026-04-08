## Requirements

### Requirement: Watcher service status API
系統 SHALL 提供 API 回傳 watcher 服務的運行狀態與監控路徑資訊。

#### Scenario: Query watcher status
- **WHEN** client 發送 `GET /api/watcher/status`
- **THEN** 系統 SHALL 回傳 JSON 包含：`running` (boolean)、`watch_paths` (陣列，每個元素含 `path`、`accessible` (boolean)、`file_count` (integer))、`scan_interval` (seconds)、`uptime_seconds`

#### Scenario: Watch path inaccessible
- **WHEN** 某個監控路徑無法存取（SMB 斷線）
- **THEN** 該路徑的 `accessible` SHALL 為 `false`，`file_count` SHALL 為 `0`

### Requirement: SMB disk usage API
系統 SHALL 提供 API 回傳 SMB 掛載路徑的磁碟空間使用狀況。

#### Scenario: Query disk usage
- **WHEN** client 發送 `GET /api/watcher/disk-usage`
- **THEN** 系統 SHALL 回傳 JSON 陣列，每個元素代表一個監控路徑的掛載點，包含：`mount_path`、`total_bytes`、`used_bytes`、`free_bytes`、`usage_percent` (0-100 浮點數)

#### Scenario: Same mount point deduplication
- **WHEN** 多個監控路徑位於同一個掛載點
- **THEN** 系統 SHALL 只回傳一筆該掛載點的空間資訊（去重）

#### Scenario: Mount point inaccessible
- **WHEN** SMB 掛載點無法存取
- **THEN** 系統 SHALL 在回應中標明該掛載點 `accessible=false`，其餘數值為 null

### Requirement: Import statistics API
系統 SHALL 提供即時匯入統計 API。

#### Scenario: Query import statistics
- **WHEN** client 發送 `GET /api/watcher/stats`
- **THEN** 系統 SHALL 回傳 JSON 包含：`today` (`total`, `success`, `failed`, `skipped`)、`this_week` (`total`, `success`, `failed`, `skipped`)、`success_rate_today` (百分比)、`success_rate_week` (百分比)

#### Scenario: No events today
- **WHEN** 今日尚無任何處理事件
- **THEN** 所有數值 SHALL 為 0，成功率 SHALL 為 null

### Requirement: Recent events list API
系統 SHALL 提供最近解析事件的分頁查詢 API。

#### Scenario: Query recent events
- **WHEN** client 發送 `GET /api/watcher/events?page=1&page_size=20`
- **THEN** 系統 SHALL 回傳分頁結果，每筆事件包含：`id`、`source_file`、`event_type` (processed/failed/skipped)、`error_message` (失敗時)、`event_datetime`；結果依 `event_datetime` 降序排列

#### Scenario: Filter events by type
- **WHEN** client 發送 `GET /api/watcher/events?event_type=failed`
- **THEN** 系統 SHALL 只回傳指定類型的事件

### Requirement: Watcher event recording
Pipeline 處理每個檔案後 SHALL 將事件寫入 `ksbody_watcher_events` 表。

#### Scenario: Successful processing event
- **WHEN** pipeline 成功處理一個 recipe body 檔案
- **THEN** 系統 SHALL 寫入一筆 event_type=processed 的紀錄，包含 source_file 和 event_datetime

#### Scenario: Failed processing event
- **WHEN** pipeline 處理一個 recipe body 檔案失敗
- **THEN** 系統 SHALL 寫入一筆 event_type=failed 的紀錄，包含 source_file、error_message（例外訊息）和 event_datetime

#### Scenario: Skipped file event
- **WHEN** watcher 發現檔案但因 mtime 未變或已處理而跳過
- **THEN** 系統 SHALL 寫入一筆 event_type=skipped 的紀錄

### Requirement: Watcher dashboard UI
前端 SHALL 新增 Watcher Tab/頁面，顯示監控儀表板。

#### Scenario: Display service status
- **WHEN** 使用者開啟 Watcher 頁面
- **THEN** 頁面頂部 SHALL 顯示 watcher 運行狀態指示燈（綠色=運行中/紅色=停止）、各監控路徑及其可用性與檔案數量

#### Scenario: Display disk usage
- **WHEN** 使用者開啟 Watcher 頁面
- **THEN** 頁面 SHALL 顯示 SMB 磁碟空間使用狀況：總容量、已使用量、剩餘空間、使用百分比（以進度條或儀表呈現）

#### Scenario: Display statistics cards
- **WHEN** 使用者開啟 Watcher 頁面
- **THEN** 頁面 SHALL 顯示統計卡片：今日匯入數、本週匯入數、今日成功率、本週成功率

#### Scenario: Display recent events
- **WHEN** 使用者開啟 Watcher 頁面
- **THEN** 頁面 SHALL 顯示最近解析事件清單，含成功/失敗/跳過的標籤，失敗事件可展開查看錯誤原因
