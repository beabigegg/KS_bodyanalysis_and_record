## ADDED Requirements

### Requirement: Delete SMB recipe files API
系統 SHALL 提供 API 刪除 SMB 上的原始 recipe body 檔案。

#### Scenario: Delete single file
- **WHEN** client 發送 `DELETE /api/watcher/files` with JSON body `{"source_files": ["/path/to/file"]}`
- **THEN** 系統 SHALL 從檔案系統刪除該檔案，清除 `FileStateStore` 中的對應標記，並回傳成功結果

#### Scenario: Batch delete files
- **WHEN** client 發送 `DELETE /api/watcher/files` with JSON body 包含多個 source_files
- **THEN** 系統 SHALL 逐一刪除檔案，回傳結果包含 `deleted` (成功清單)、`errors` (失敗清單及原因)

#### Scenario: File does not exist
- **WHEN** 要刪除的檔案在檔案系統上不存在
- **THEN** 系統 SHALL 在回應的 `errors` 陣列中標明該檔案不存在，不視為致命錯誤

#### Scenario: Permission denied
- **WHEN** 系統無權限刪除 SMB 上的檔案
- **THEN** 系統 SHALL 回傳 `errors` 陣列中標明權限不足

#### Scenario: File path validation
- **WHEN** 要刪除的檔案路徑不在任何已配置的監控路徑下
- **THEN** 系統 SHALL 回傳 HTTP 400，拒絕刪除操作（防止路徑穿越攻擊）

### Requirement: Export recipe body as tar.gz API
系統 SHALL 提供 API 將 SMB 上的 recipe body 檔案以標準 `.tar.gz` 格式串流下載。

#### Scenario: Download single file
- **WHEN** client 發送 `GET /api/watcher/files/download?path=/path/to/file`
- **THEN** 系統 SHALL 以 `StreamingResponse` 回傳檔案內容，Content-Type 為 `application/gzip`，Content-Disposition 為 `attachment; filename="<original_filename>.tar.gz"`

#### Scenario: File not found
- **WHEN** 指定的檔案不存在
- **THEN** 系統 SHALL 回傳 HTTP 404

#### Scenario: Path validation
- **WHEN** 指定的路徑不在任何已配置的監控路徑下
- **THEN** 系統 SHALL 回傳 HTTP 400（防止路徑穿越攻擊）

### Requirement: File management UI
前端 SHALL 提供檔案刪除與匯出下載的操作介面。

#### Scenario: Delete files from file browser
- **WHEN** 使用者在檔案瀏覽器勾選檔案後點擊「刪除」按鈕
- **THEN** 系統 SHALL 顯示確認對話框，列出即將刪除的檔案數量，確認後執行刪除並刷新列表

#### Scenario: Download files from file browser
- **WHEN** 使用者在檔案瀏覽器點擊某檔案的「下載」按鈕
- **THEN** 瀏覽器 SHALL 開始下載該檔案的 `.tar.gz` 版本

#### Scenario: Batch download
- **WHEN** 使用者勾選多個檔案後點擊「匯出下載」
- **THEN** 系統 SHALL 逐一觸發下載（或以 zip 打包多個 tar.gz 後下載）
