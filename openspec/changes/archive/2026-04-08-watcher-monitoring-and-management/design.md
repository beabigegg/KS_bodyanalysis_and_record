## Context

目前 watcher 模組（`ksbody/watcher/`）負責監控 SMB 掛載路徑上的 recipe body 檔案，偵測到新檔案後透過 `RecipePipeline` 解析並寫入 MySQL。但整個流程對使用者不透明：無法查看 watcher 狀態、無法瀏覽檔案、無法管理已匯入的 recipe。

現有架構：
- **Pipeline 服務**：`run_pipeline()` 啟動 watcher + scanner，透過 callback 處理檔案
- **State 管理**：`FileStateStore` 以 JSON 記錄已處理檔案的 mtime
- **Web 服務**：FastAPI 應用，已有 imports/compare/trend/r2r/yield_corr 等 API
- **前端**：React SPA，透過 `ksbody/web/frontend/dist/` 提供

約束：pipeline 和 web 是獨立 process（由 `ProcessManager` 管理），watcher 狀態資訊需要跨 process 共享。

## Goals / Non-Goals

**Goals:**
- 讓使用者透過 Web UI 完整掌握 watcher 運行狀態與檔案處理情況
- 提供 recipe body 檔案的管理操作：重新解析、刪除、匯出下載
- 提供自動清理排程功能，減少人工維運負擔
- 建立 recipe 唯一識別機制

**Non-Goals:**
- 不做 watcher 的啟動/停止控制（仍由 `start.sh` 管理）
- 不做 SMB 掛載管理（仍由 `mount-smb.sh` 管理）
- 不做 recipe 內容的線上編輯
- 不做跨 server 的分散式 watcher 管理

## Decisions

### 1. 跨 Process 狀態共享：使用 DB 而非共享記憶體

**選擇**：新增 `ksbody_watcher_events` 表記錄每次檔案處理事件（成功/失敗/跳過），取代純靠 `processed_files.json`。

**理由**：
- Pipeline 和 Web 是獨立 process，共享記憶體需要額外 IPC 機制（如 Redis、shared memory）
- DB 是兩個 process 都能存取的現有基礎設施
- 事件紀錄有歷史價值，JSON state file 只記最新 mtime

**替代方案**：
- Redis：引入新依賴，對此規模的系統 overkill
- 共享 JSON 檔：多 process 寫入有 race condition 風險
- Pipeline 內嵌 HTTP API：增加架構複雜度

### 2. 背景任務管理：使用 in-memory task tracker + DB 持久化

**選擇**：重新解析任務在 pipeline process 中以 thread pool 執行，任務狀態寫入 DB（`ksbody_reparse_tasks` 表），Web process 透過 DB 查詢進度。

**理由**：
- 重新解析本質上需要 pipeline 的 `RecipePipeline.process()` 方法
- Web process 需要能查詢任務進度
- DB 作為中介可以解耦兩個 process

**觸發機制**：Web API 寫入 reparse 請求到 DB → pipeline 的 scanner 迴圈檢查待處理請求 → 執行重新解析 → 更新狀態。

### 3. 檔案瀏覽：直接掃描檔案系統 + 比對 DB 狀態

**選擇**：API 請求時即時掃描監控路徑，與 DB 事件紀錄比對得出每個檔案的狀態。

**理由**：
- 檔案系統是唯一真實來源（SMB 上的檔案可能被外部增刪）
- 分頁透過排序後 offset/limit 實現
- 快取可日後加入，先以正確性為優先

**替代方案**：
- 定期掃描寫入 DB：增加資料同步複雜度，可能不夠即時

### 4. 自動清理排程：基於空間使用率，pipeline process 內建 scheduler

**選擇**：在 pipeline process 中新增清理排程線程，定期檢查 SMB 掛載路徑的磁碟使用率。當使用率超過設定閾值時，從最舊的 recipe body 開始刪除直到使用率降至閾值以下。設定存放於 DB 表（`ksbody_cleanup_config`），Web UI 讀寫此表。刪除操作記錄到 `ksbody_cleanup_log` 表。

**理由**：
- 基於空間使用率比基於天數更貼近實際需求：磁碟滿了才需要清理
- 從最舊的開始刪除，確保最新的 recipe 始終可用
- 清理需要存取檔案系統（刪除 SMB 檔案），pipeline process 已具備此存取能力
- 設定存 DB 而非 `.env`，支援 Web UI 動態修改不需重啟服務
- 排程間隔固定（每小時檢查一次），根據設定決定是否執行
- 刪除紀錄持久化到 DB，便於追蹤與稽核

**磁碟使用率取得方式**：使用 `shutil.disk_usage(path)` 取得 SMB 掛載點的 total/used/free，計算使用百分比。對每個 watch_path 取其掛載點的使用率。

### 5. 匯出下載：Web API 串流回傳

**選擇**：`GET /api/watcher/files/download?path=<source_file>` 讀取 SMB 上的原始檔案，以 `StreamingResponse` 回傳，Content-Disposition 設定為 `<filename>.tar.gz`。

**理由**：
- 原始檔案本身就是 gzip tar 格式，只需加副檔名
- 串流回傳避免將整個檔案載入記憶體
- 不需解壓重新打包

### 6. Recipe 唯一識別：複合邏輯識別，不加 DB unique constraint

**選擇**：唯一識別為 `source_file` + `import_datetime` 的組合。不在 DB 加 unique constraint，因為每次解析都是有意產生的新紀錄。

**理由**：
- 同一檔案的每次解析都有不同的 `import_datetime`
- auto-increment `id` 作為技術主鍵已足夠
- 新增 `idx_ksbody_import_source_time` 索引（`source_file`, `import_datetime`）加速查詢

## Risks / Trade-offs

**[即時掃描檔案系統可能效能不佳]** → 若監控路徑下檔案數量過大（>10,000），API 回應時間可能過長。Mitigation：分頁限制每頁數量、未來可加入 DB 快取層。

**[Pipeline process 重啟時任務丟失]** → Reparse 任務以 DB 持久化，pipeline 重啟後可恢復待處理任務。

**[SMB 檔案刪除不可逆]** → 前端強制確認對話框；自動清理有明確的保留天數設定與開關。

**[跨 process 通訊延遲]** → Web 寫入 DB → Pipeline 讀取 DB 有輪詢延遲（scanner 間隔）。Reparse 請求不會立即執行，需等待下一次 scanner 迴圈（最長 SCAN_INTERVAL 秒）。可接受，因為重新解析本身就不是即時需求。

## New Database Tables

### `ksbody_watcher_events`
記錄每次檔案處理事件：
- `id`, `source_file`, `event_type` (discovered/processed/failed/skipped), `error_message`, `event_datetime`
- 索引：`(source_file, event_datetime)`, `(event_type, event_datetime)`

### `ksbody_reparse_tasks`
重新解析任務佇列：
- `id`, `source_file`, `status` (pending/running/completed/failed), `error_message`, `created_at`, `started_at`, `completed_at`
- 索引：`(status, created_at)`

### `ksbody_cleanup_config`
清理排程設定（單列表）：
- `id`, `enabled` (boolean), `threshold_percent` (integer, 0-100), `last_run_at` (datetime), `updated_at`

### `ksbody_cleanup_log`
清理刪除紀錄：
- `id`, `source_file`, `file_size_bytes` (bigint), `file_mtime` (datetime), `deleted_at` (datetime), `trigger` (auto/manual)
- 索引：`(deleted_at)`

## API Endpoints Overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/watcher/status` | Watcher 服務狀態 + 監控路徑資訊 |
| GET | `/api/watcher/stats` | 即時統計（今日/本週匯入數、成功率） |
| GET | `/api/watcher/events` | 最近解析事件清單（分頁） |
| GET | `/api/watcher/files` | 檔案瀏覽器（分頁、含狀態） |
| GET | `/api/watcher/files/download` | 匯出下載（串流回傳 .tar.gz） |
| DELETE | `/api/watcher/files` | 刪除 SMB 原始檔案（批次） |
| POST | `/api/watcher/reparse` | 提交重新解析請求 |
| GET | `/api/watcher/reparse` | 查詢重新解析任務進度 |
| GET | `/api/watcher/cleanup/config` | 讀取清理排程設定 |
| PUT | `/api/watcher/cleanup/config` | 更新清理排程設定 |
| GET | `/api/watcher/cleanup/log` | 查詢清理刪除紀錄（分頁） |
| GET | `/api/watcher/disk-usage` | 查詢 SMB 磁碟空間使用狀況 |
