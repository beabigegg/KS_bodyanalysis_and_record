## ADDED Requirements

### Requirement: Cleanup configuration API
系統 SHALL 提供 API 讀取與更新自動清理排程設定。

#### Scenario: Read cleanup config
- **WHEN** client 發送 `GET /api/watcher/cleanup/config`
- **THEN** 系統 SHALL 回傳 JSON 包含：`enabled` (boolean)、`threshold_percent` (integer, 0-100)、`last_run_at` (datetime or null)、`updated_at` (datetime)

#### Scenario: Update cleanup config
- **WHEN** client 發送 `PUT /api/watcher/cleanup/config` with JSON body `{"enabled": true, "threshold_percent": 80}`
- **THEN** 系統 SHALL 更新 `ksbody_cleanup_config` 表，回傳更新後的完整設定

#### Scenario: Invalid threshold percent
- **WHEN** client 發送 threshold_percent 不在 1-99 範圍內
- **THEN** 系統 SHALL 回傳 HTTP 400 並說明 threshold_percent 必須為 1-99 之間的整數

#### Scenario: First-time config initialization
- **WHEN** `ksbody_cleanup_config` 表為空
- **THEN** 系統 SHALL 使用預設值初始化：`enabled=false`、`threshold_percent=80`

### Requirement: Automatic cleanup based on disk usage threshold
Pipeline process SHALL 定期檢查 SMB 磁碟使用率，當超過閾值時從最舊的 recipe body 開始刪除。

#### Scenario: Cleanup triggered by threshold exceeded
- **WHEN** 清理排程啟用且磁碟使用率超過 `threshold_percent`
- **THEN** 系統 SHALL 掃描監控路徑下所有 recipe body 檔案，依檔案修改時間（mtime）由舊到新排序，逐一刪除直到磁碟使用率降至閾值以下，每個刪除操作 SHALL 記錄到 `ksbody_cleanup_log` 表

#### Scenario: Cleanup when under threshold
- **WHEN** 清理排程啟用但磁碟使用率未超過閾值
- **THEN** 系統 SHALL 跳過清理，不做任何操作

#### Scenario: Cleanup when disabled
- **WHEN** 清理排程未啟用
- **THEN** 系統 SHALL 跳過清理，不做任何操作

#### Scenario: Cleanup check interval
- **WHEN** pipeline process 運行中
- **THEN** 系統 SHALL 每小時檢查一次磁碟使用率，並更新 `last_run_at`

#### Scenario: File already deleted externally
- **WHEN** 清理過程中某個 recipe body 檔案已被外部刪除
- **THEN** 系統 SHALL 記錄 debug 日誌並跳過該檔案，不視為錯誤，不寫入 cleanup_log

#### Scenario: Cleanup logging
- **WHEN** 清理執行完成
- **THEN** 系統 SHALL 記錄 info 日誌，包含：刪除前使用率、刪除後使用率、刪除的檔案數量、釋放的空間大小

### Requirement: Cleanup deletion log
系統 SHALL 記錄每次自動或手動刪除 SMB 檔案的紀錄。

#### Scenario: Record auto cleanup deletion
- **WHEN** 自動清理刪除一個 recipe body 檔案
- **THEN** 系統 SHALL 寫入一筆 `ksbody_cleanup_log` 紀錄，包含：`source_file`、`file_size_bytes`、`file_mtime`、`deleted_at`、`trigger=auto`

#### Scenario: Record manual deletion
- **WHEN** 使用者透過 API 手動刪除 SMB 檔案
- **THEN** 系統 SHALL 寫入一筆 `ksbody_cleanup_log` 紀錄，包含：`source_file`、`file_size_bytes`、`file_mtime`、`deleted_at`、`trigger=manual`

#### Scenario: Query cleanup log API
- **WHEN** client 發送 `GET /api/watcher/cleanup/log?page=1&page_size=50`
- **THEN** 系統 SHALL 回傳分頁結果，每筆包含完整刪除紀錄，依 `deleted_at` 降序排列

#### Scenario: Filter cleanup log by trigger type
- **WHEN** client 發送 `GET /api/watcher/cleanup/log?trigger=auto`
- **THEN** 系統 SHALL 只回傳自動清理產生的刪除紀錄

### Requirement: Cleanup configuration UI
前端 SHALL 在 Watcher 頁面提供清理排程設定介面。

#### Scenario: Display cleanup settings
- **WHEN** 使用者開啟 Watcher 頁面的清理設定區塊
- **THEN** 頁面 SHALL 顯示：啟用/停用開關、空間使用閾值百分比輸入框、目前磁碟使用率、上次執行時間

#### Scenario: Update cleanup settings
- **WHEN** 使用者修改設定後點擊儲存
- **THEN** 系統 SHALL 呼叫 PUT API 更新設定，並顯示成功通知

#### Scenario: Validation
- **WHEN** 使用者輸入無效的閾值百分比（非 1-99 整數）
- **THEN** 前端 SHALL 顯示驗證錯誤，不發送請求

#### Scenario: Display cleanup log
- **WHEN** 使用者開啟清理設定區塊
- **THEN** 頁面 SHALL 顯示最近的刪除紀錄清單（檔案名稱、大小、刪除時間、觸發方式），支援分頁
