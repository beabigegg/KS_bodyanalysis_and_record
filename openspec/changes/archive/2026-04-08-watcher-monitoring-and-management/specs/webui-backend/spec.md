## ADDED Requirements

### Requirement: Watcher monitoring API routes
Web 服務 SHALL 提供 watcher 監控相關的 API routes，掛載於 `/api/watcher` 前綴。

#### Scenario: Register watcher routes
- **WHEN** FastAPI 應用啟動
- **THEN** 系統 SHALL 註冊 watcher router，提供 status/stats/events/files/reparse/cleanup 等 endpoints

#### Scenario: Watcher routes module location
- **WHEN** 開發者需要修改 watcher API
- **THEN** routes SHALL 位於 `ksbody/web/routes/watcher.py`

### Requirement: FileStateStore dependency injection
Web API SHALL 能存取 `FileStateStore` 實例，用於清除已處理標記。

#### Scenario: Access state store from web API
- **WHEN** 刪除或重新解析 API 需要操作 FileStateStore
- **THEN** 系統 SHALL 透過 FastAPI dependency injection 提供 `FileStateStore` 實例，使用與 pipeline process 相同的 `STATE_FILE` 路徑

#### Scenario: Concurrent state file access
- **WHEN** Web process 和 pipeline process 同時存取 state file
- **THEN** `FileStateStore` 的 file-level 寫入 SHALL 保證原子性（寫入完整 JSON 後才替換）

### Requirement: Database tables for watcher features
Web 服務啟動時 SHALL 確保 watcher 相關的新資料表已建立。

#### Scenario: Create watcher event table
- **WHEN** 服務啟動
- **THEN** 系統 SHALL 建立 `ksbody_watcher_events` 表（若不存在），包含 `id`, `source_file`, `event_type`, `error_message`, `event_datetime` 欄位

#### Scenario: Create reparse tasks table
- **WHEN** 服務啟動
- **THEN** 系統 SHALL 建立 `ksbody_reparse_tasks` 表（若不存在），包含 `id`, `source_file`, `status`, `error_message`, `created_at`, `started_at`, `completed_at` 欄位

#### Scenario: Create cleanup config table
- **WHEN** 服務啟動
- **THEN** 系統 SHALL 建立 `ksbody_cleanup_config` 表（若不存在），包含 `id`, `enabled`, `threshold_percent`, `last_run_at`, `updated_at` 欄位

#### Scenario: Create cleanup log table
- **WHEN** 服務啟動
- **THEN** 系統 SHALL 建立 `ksbody_cleanup_log` 表（若不存在），包含 `id`, `source_file`, `file_size_bytes`, `file_mtime`, `deleted_at`, `trigger` 欄位
