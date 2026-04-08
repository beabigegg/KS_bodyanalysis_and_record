## Requirements

### Requirement: File listing API with pagination
系統 SHALL 提供監控路徑下 recipe body 檔案的分頁列表 API。

#### Scenario: List files with pagination
- **WHEN** client 發送 `GET /api/watcher/files?page=1&page_size=50`
- **THEN** 系統 SHALL 掃描所有監控路徑，回傳符合 recipe body 檔名格式的檔案清單，每筆包含：`path`（完整路徑）、`filename`、`size_bytes`、`mtime`（檔案修改時間）、`status`（parsed/unparsed/failed）、`last_parsed_at`（最近一次成功解析時間，若有）
- **AND** 回傳 `total_count`（總檔案數）、`page`、`page_size`

#### Scenario: File status determination
- **WHEN** 系統取得檔案列表
- **THEN** 每個檔案的 status SHALL 依以下邏輯判定：
  - `parsed`：`ksbody_watcher_events` 中存在 event_type=processed 的紀錄
  - `failed`：最近一筆事件為 event_type=failed
  - `unparsed`：無任何事件紀錄

#### Scenario: Filter files by status
- **WHEN** client 發送 `GET /api/watcher/files?status=unparsed`
- **THEN** 系統 SHALL 只回傳指定狀態的檔案

#### Scenario: Filter files by path
- **WHEN** client 發送 `GET /api/watcher/files?watch_path=/mnt/eap_recipe/WBK_ConnX Elite`
- **THEN** 系統 SHALL 只回傳指定監控路徑下的檔案

#### Scenario: Watch path inaccessible during listing
- **WHEN** 某個監控路徑在掃描時無法存取
- **THEN** 系統 SHALL 跳過該路徑並在回應中包含 `warnings` 陣列說明哪些路徑不可用

### Requirement: File browser UI with selection
前端 SHALL 提供檔案瀏覽器元件，支援分頁與勾選。

#### Scenario: Display file list
- **WHEN** 使用者切換到檔案瀏覽器區塊
- **THEN** 頁面 SHALL 以表格形式顯示檔案列表，每列含：勾選框、檔案名稱、大小、修改時間、狀態標籤（已解析/未解析/失敗）、最近解析時間

#### Scenario: Paginate file list
- **WHEN** 檔案總數超過每頁顯示數量
- **THEN** 頁面底部 SHALL 顯示分頁控制項，使用者可切換頁面

#### Scenario: Filter by status
- **WHEN** 使用者選擇狀態篩選條件
- **THEN** 檔案列表 SHALL 只顯示符合條件的檔案

#### Scenario: Select files for batch operations
- **WHEN** 使用者勾選一或多個檔案
- **THEN** 操作工具列 SHALL 出現，顯示已選數量及可用操作（重新解析、刪除、匯出下載）
