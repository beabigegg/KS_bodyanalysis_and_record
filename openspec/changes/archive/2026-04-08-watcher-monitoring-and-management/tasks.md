## 1. Database Schema & Infrastructure

- [x] 1.1 新增 `ksbody_watcher_events` 表定義到 `ksbody/db/schema.py`（id, source_file, event_type, error_message, event_datetime + 索引）
- [x] 1.2 新增 `ksbody_reparse_tasks` 表定義到 `ksbody/db/schema.py`（id, source_file, status, error_message, created_at, started_at, completed_at + 索引）
- [x] 1.3 新增 `ksbody_cleanup_config` 表定義到 `ksbody/db/schema.py`（id, enabled, threshold_percent, last_run_at, updated_at）
- [x] 1.3.1 新增 `ksbody_cleanup_log` 表定義到 `ksbody/db/schema.py`（id, source_file, file_size_bytes, file_mtime, deleted_at, trigger + 索引）
- [x] 1.4 將新表加入 `ALL_TABLES` 列表，確保 `metadata.create_all()` 自動建表
- [x] 1.5 新增 `idx_ksbody_import_source_time` 索引（source_file, import_datetime）到 recipe_import 表

## 2. FileStateStore 擴充

- [x] 2.1 在 `FileStateStore` 新增 `clear(file_path)` 方法：移除指定路徑的已處理標記並持久化
- [x] 2.2 在 `FileStateStore` 新增 `clear_many(file_paths)` 方法：批次移除多個路徑的標記並持久化
- [x] 2.3 為新方法撰寫單元測試

## 3. Watcher 事件紀錄

- [x] 3.1 新增 `WatcherEventRepository` 類別到 `ksbody/db/repository.py`（或新檔案），提供 `record_event(source_file, event_type, error_message)` 方法
- [x] 3.2 修改 `pipeline/runner.py` 的 `build_callback()`：成功時記錄 processed 事件，失敗時記錄 failed 事件
- [x] 3.3 修改 `watcher/handler.py` 和 `watcher/scanner.py`：跳過檔案時記錄 skipped 事件
- [x] 3.4 為事件紀錄撰寫單元測試

## 4. Watcher 狀態查詢 API

- [x] 4.1 新增 `ksbody/web/routes/watcher.py` router 模組
- [x] 4.2 實作 `GET /api/watcher/status`：回傳 watcher 運行狀態、監控路徑列表與可用性、各路徑檔案數量
- [x] 4.2.1 實作 `GET /api/watcher/disk-usage`：使用 `shutil.disk_usage()` 回傳 SMB 掛載點的 total/used/free/usage_percent，同一掛載點去重
- [x] 4.3 實作 `GET /api/watcher/stats`：從 watcher_events 表統計今日/本週匯入數量與成功率
- [x] 4.4 實作 `GET /api/watcher/events`：分頁查詢解析事件（支援 event_type 過濾）
- [x] 4.5 在 `app.py` 註冊 watcher router

## 5. 檔案瀏覽 API

- [x] 5.1 實作 `GET /api/watcher/files`：掃描監控路徑下的 recipe body 檔案，比對 DB 事件紀錄得出狀態，支援分頁與狀態/路徑篩選
- [x] 5.2 實作路徑驗證工具函式：確認檔案路徑在已配置的監控路徑之下（防止路徑穿越）

## 6. 重新解析功能

- [x] 6.1 實作 `POST /api/watcher/reparse`：接受 source_files 陣列，建立 reparse_tasks 紀錄，清除 FileStateStore 標記
- [x] 6.2 實作 `GET /api/watcher/reparse`：查詢 reparse 任務進度（支援 task_ids 過濾）
- [x] 6.3 修改 `pipeline/runner.py`：在 scanner 迴圈中加入 reparse task 檢查與執行邏輯
- [x] 6.4 處理 pipeline 重啟時 status=running 的任務重設為 pending

## 7. 檔案管理 API（刪除 & 匯出）

- [x] 7.1 實作 `DELETE /api/watcher/files`：批次刪除 SMB 檔案，含路徑驗證、FileStateStore 清除、錯誤回報，並寫入 cleanup_log（trigger=manual）
- [x] 7.2 實作 `GET /api/watcher/files/download`：串流回傳指定 recipe body 檔案，Content-Disposition 加 `.tar.gz` 副檔名
- [x] 7.3 為路徑驗證與刪除邏輯撰寫單元測試

## 8. recipe-import-delete 擴充

- [x] 8.1 修改 `DELETE /api/imports/{import_id}` 與 `DELETE /api/imports/batch`：支援 `clear_state` 參數，清除 FileStateStore 對應標記
- [x] 8.2 Web API 新增 FileStateStore dependency injection（FastAPI DI）

## 9. 自動清理排程

- [x] 9.1 實作 `GET /api/watcher/cleanup/config` 和 `PUT /api/watcher/cleanup/config`：讀寫清理排程設定（threshold_percent）
- [x] 9.2 在 pipeline process 新增清理排程線程：每小時檢查磁碟使用率，超過閾值時從最舊的 recipe body 開始刪除，直到使用率降至閾值以下
- [x] 9.3 實作首次設定初始化邏輯（enabled=false, threshold_percent=80）
- [x] 9.4 每次刪除寫入 `ksbody_cleanup_log`（trigger=auto），記錄 source_file、file_size_bytes、file_mtime、deleted_at
- [x] 9.5 實作 `GET /api/watcher/cleanup/log`：分頁查詢刪除紀錄，支援 trigger 類型過濾
- [x] 9.6 為清理邏輯撰寫單元測試

## 10. 前端 — Watcher 頁面骨架

- [x] 10.1 在前端路由新增 Watcher 頁面，導覽列新增對應 Tab
- [x] 10.2 建立頁面佈局：服務狀態區、統計卡片區、事件清單區、檔案瀏覽器區、清理設定區

## 11. 前端 — 監控儀表板

- [x] 11.1 實作服務狀態元件：運行狀態指示燈、監控路徑列表與可用性
- [x] 11.1.1 實作 SMB 磁碟空間元件：總容量、已使用量、剩餘空間、使用百分比（進度條或儀表）
- [x] 11.2 實作統計卡片元件：今日/本週匯入數、成功率
- [x] 11.3 實作最近事件清單元件：事件列表（含狀態標籤）、失敗事件可展開查看錯誤訊息、分頁

## 12. 前端 — 檔案瀏覽器

- [x] 12.1 實作檔案列表表格元件：勾選框、檔名、大小、修改時間、狀態標籤、解析時間
- [x] 12.2 實作分頁控制項
- [x] 12.3 實作狀態篩選功能
- [x] 12.4 實作批次操作工具列：顯示已選數量、重新解析/刪除/下載按鈕

## 13. 前端 — 操作功能

- [x] 13.1 實作重新解析功能：提交請求、進度 polling（每 5 秒）、進度列表顯示、完成後自動刷新
- [x] 13.2 實作刪除確認對話框：顯示待刪除檔案數量、確認後執行刪除
- [x] 13.3 實作匯出下載功能：單檔下載與批次下載觸發
- [x] 13.4 實作 import 刪除對話框新增「清除已處理標記」checkbox 選項

## 14. 前端 — 清理排程設定

- [x] 14.1 實作清理設定元件：啟用/停用開關、空間使用閾值百分比輸入框、目前磁碟使用率顯示、上次執行時間、儲存按鈕
- [x] 14.2 實作前端驗證：閾值百分比須為 1-99 整數
- [x] 14.3 實作刪除紀錄清單元件：顯示最近的刪除紀錄（檔案名稱、大小、刪除時間、觸發方式），支援分頁

## 15. 整合測試與驗證

- [x] 15.1 後端 API 整合測試：watcher status/stats/events/files/reparse/cleanup endpoints
- [x] 15.2 端對端測試：檔案瀏覽 → 重新解析 → 查看進度 → 驗證結果
- [x] 15.3 驗證路徑穿越防護：確認非法路徑被拒絕
