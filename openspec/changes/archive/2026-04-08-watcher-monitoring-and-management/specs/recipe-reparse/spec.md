## ADDED Requirements

### Requirement: Submit reparse request API
系統 SHALL 提供 API 接受重新解析請求。

#### Scenario: Submit reparse for selected files
- **WHEN** client 發送 `POST /api/watcher/reparse` with JSON body `{"source_files": ["/path/to/file1", "/path/to/file2"]}`
- **THEN** 系統 SHALL 為每個檔案建立一筆 `ksbody_reparse_tasks` 紀錄（status=pending），清除對應的 `FileStateStore` 已處理標記，並回傳 task IDs

#### Scenario: File does not exist
- **WHEN** 請求中的某個 source_file 在檔案系統上不存在
- **THEN** 系統 SHALL 跳過該檔案，在回應的 `errors` 陣列中標明，並繼續處理其他檔案

#### Scenario: File already has pending reparse
- **WHEN** 請求的 source_file 已有 status=pending 或 status=running 的 reparse task
- **THEN** 系統 SHALL 跳過該檔案，在回應的 `skipped` 陣列中標明原因

### Requirement: Reparse task execution by pipeline
Pipeline process SHALL 定期檢查並執行待處理的重新解析任務。

#### Scenario: Execute pending reparse tasks
- **WHEN** pipeline 的 scanner 迴圈執行時
- **THEN** 系統 SHALL 查詢 `ksbody_reparse_tasks` 中 status=pending 的任務，依 created_at 順序逐一執行 `RecipePipeline.process()`，執行前將 status 更新為 running，完成後更新為 completed 或 failed

#### Scenario: Reparse task fails
- **WHEN** 重新解析過程中發生例外
- **THEN** 系統 SHALL 將任務 status 更新為 failed，記錄 error_message，並繼續處理下一個任務

#### Scenario: Pipeline restart with pending tasks
- **WHEN** pipeline process 重啟時存在 status=running 的任務
- **THEN** 系統 SHALL 將這些任務 status 重設為 pending，等待下次迴圈重新執行

### Requirement: Reparse progress query API
系統 SHALL 提供 API 查詢重新解析任務的進度。

#### Scenario: Query reparse task status
- **WHEN** client 發送 `GET /api/watcher/reparse?task_ids=1,2,3`
- **THEN** 系統 SHALL 回傳每個任務的狀態：`id`、`source_file`、`status` (pending/running/completed/failed)、`error_message`、`created_at`、`started_at`、`completed_at`

#### Scenario: Query all active reparse tasks
- **WHEN** client 發送 `GET /api/watcher/reparse`（不帶 task_ids）
- **THEN** 系統 SHALL 回傳所有非 completed 的任務清單（pending + running + failed），依 created_at 降序

### Requirement: Reparse UI interaction
前端 SHALL 提供重新解析的操作介面與進度顯示。

#### Scenario: Trigger reparse from file browser
- **WHEN** 使用者在檔案瀏覽器勾選檔案後點擊「重新解析」按鈕
- **THEN** 系統 SHALL 發送 reparse 請求，顯示已提交的通知，並在操作完成前以 polling 方式更新任務進度

#### Scenario: Display reparse progress
- **WHEN** 有進行中的重新解析任務
- **THEN** 頁面 SHALL 顯示任務進度列表（檔案名稱、狀態、錯誤訊息），每 5 秒自動刷新

#### Scenario: Reparse completed
- **WHEN** 所有提交的重新解析任務完成
- **THEN** 檔案瀏覽器 SHALL 自動刷新檔案狀態
