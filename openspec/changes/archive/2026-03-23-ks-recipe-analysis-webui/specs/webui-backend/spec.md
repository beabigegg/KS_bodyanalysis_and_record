## ADDED Requirements

### Requirement: FastAPI application with .env configuration
系統 SHALL 建立 FastAPI 應用，所有配置由 .env 檔案管理。

#### Scenario: Load configuration from .env
- **WHEN** 應用啟動
- **THEN** 系統 SHALL 從 .env 載入 APP_PORT、APP_MODE（dev/prod）、MySQL 連線、Oracle 連線（可選）、認證設定

#### Scenario: Serve frontend as static files (monolithic)
- **WHEN** 應用啟動
- **THEN** 系統 SHALL 由 FastAPI 統一託管 frontend/dist 靜態檔案和 API 路由，所有請求透過單一 port 伺服，符合 IT 單體式架構規範

### Requirement: REST API endpoints
系統 SHALL 提供結構化的 REST API 端點。

#### Scenario: List imports endpoint
- **WHEN** GET /api/imports（支援 query params 篩選）
- **THEN** 回傳分頁的 recipe import 記錄列表

#### Scenario: Get import detail endpoint
- **WHEN** GET /api/imports/{id}/params
- **THEN** 回傳該 import 的所有參數，依 file_type 分組

#### Scenario: Compare endpoint
- **WHEN** POST /api/compare 帶入多個 import_id
- **THEN** 回傳各 import 之間的參數差異

#### Scenario: Trend endpoint
- **WHEN** GET /api/trend 帶入 machine_id、product_type、param_name、時間範圍
- **THEN** 回傳時間序列資料

#### Scenario: R2R statistics endpoint
- **WHEN** GET /api/r2r/stats 帶入機台、產品、參數
- **THEN** 回傳 SPC 統計值（mean、std_dev、UCL、LCL、Cp、Cpk）

### Requirement: Database connection management
系統 SHALL 使用 SQLAlchemy 連線池管理 MySQL 連線，重用現有 ksbody_ schema 定義。

#### Scenario: Share schema with parser
- **WHEN** 應用啟動
- **THEN** 系統 SHALL import 現有 db/schema.py 的表定義，不重複定義

#### Scenario: Read-only access
- **WHEN** API 處理查詢
- **THEN** 系統 SHALL 僅執行 SELECT 查詢，不對 ksbody_ 表進行任何寫入操作

### Requirement: API response format
系統 SHALL 統一 API 回應格式。

#### Scenario: Successful response
- **WHEN** API 請求成功
- **THEN** 回傳 JSON 格式 `{"data": ..., "total": N}` 結構

#### Scenario: Error response
- **WHEN** API 請求失敗
- **THEN** 回傳 HTTP 錯誤碼和 `{"detail": "error message"}` 結構
