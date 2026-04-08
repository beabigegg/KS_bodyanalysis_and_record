## Why

目前 watcher 僅具備基本的檔案偵測與解析功能，缺乏運行狀態的可見性：使用者無法得知 watcher 發現了哪些檔案、解析了哪些、失敗了哪些。同時缺少對已匯入 recipe 的管理操作（強制重新解析、刪除 SMB 原始檔案、匯出下載）以及自動清理過期檔案的機制。這些在實際生產環境中都是必要的日常維運功能。

## What Changes

- 新增 Watcher 監控面板（前端新 Tab + 後端 API），顯示服務狀態、監控路徑、即時統計、解析歷史、檔案瀏覽器
- 新增檔案瀏覽功能：瀏覽監控路徑下所有 recipe body 檔案，顯示每個檔案的狀態（已解析/未解析/失敗），支援分頁
- 新增重新解析功能：從檔案瀏覽清單勾選 recipe body → 背景執行重新解析，頁面顯示進度
- 新增 SMB 原始檔案刪除功能（確認後直接刪除）
- 新增匯出下載功能：將 SMB 上的 recipe body（無副檔名 gzip tar）轉成標準 `.tar.gz` 提供下載
- 新增 SMB 磁碟空間監控：在監控面板顯示 SMB 掛載路徑的總容量、已使用量、使用百分比
- 新增自動清理排程：在 Web UI 設定空間使用百分比閾值與開關，當使用空間達到閾值時從最舊的 recipe body 開始刪除，並保留刪除紀錄
- 明確 recipe 唯一識別邏輯：`source_file`（路徑）+ recipe 檔名（含 timestamp）+ `import_datetime`（解析時間），每次解析產生獨立紀錄

## Capabilities

### New Capabilities
- `watcher-dashboard`: Watcher 監控面板 — 服務狀態、監控路徑統計、SMB 磁碟空間使用量、即時匯入統計（今日/本週數量與成功率）、最近解析清單（成功/失敗/跳過及錯誤原因）
- `watcher-file-browser`: 檔案瀏覽器 — 瀏覽監控路徑下所有 recipe body 檔案，顯示各檔案解析狀態，支援分頁載入
- `recipe-reparse`: 重新解析 — 從檔案瀏覽清單勾選已處理的 recipe body，清除 state 標記後背景重跑 pipeline，頁面顯示進度
- `recipe-file-management`: Recipe 檔案管理 — SMB 原始檔案刪除（確認對話框）及匯出下載（轉成標準 `.tar.gz`）
- `recipe-auto-cleanup`: 自動清理排程 — Web UI 設定空間使用百分比閾值與開關，當 SMB 使用空間達到閾值時從最舊的 recipe body 開始刪除，並記錄刪除歷史

### Modified Capabilities
- `folder-watcher`: 需暴露 watcher 內部狀態（運行狀態、已處理檔案清單、失敗紀錄）供監控 API 讀取
- `recipe-import-delete`: 刪除 MySQL 解析結果時新增選項：使用者可選擇是否同時清除 state 中的已處理標記
- `webui-backend`: 新增 watcher 監控、檔案瀏覽、重新解析、檔案管理、自動清理等 API endpoints

## Impact

- **後端**：新增多個 API endpoints（watcher 狀態、檔案列表、重新解析、檔案刪除、匯出下載、清理排程設定）；watcher 模組需新增狀態追蹤機制（解析歷史、失敗紀錄）；需新增背景任務管理（重新解析進度追蹤）；需新增排程任務（自動清理）
- **前端**：導覽列新增 Watcher Tab/頁面，包含監控儀表板、檔案瀏覽器、管理操作面板、清理排程設定
- **資料庫**：可能需要新增表或欄位來記錄解析失敗歷史、清理排程設定；明確 recipe 唯一識別的複合索引
- **檔案系統**：涉及 SMB 路徑上的檔案刪除操作，需注意權限和錯誤處理
- **State 管理**：`FileStateStore` 需支援清除特定檔案的已處理標記（供重新解析使用）
