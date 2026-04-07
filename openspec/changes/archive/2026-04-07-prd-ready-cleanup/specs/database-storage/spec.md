## MODIFIED Requirements

### Requirement: Create recipe_import master table
系統 SHALL 在 MySQL 建立 recipe_import 主表，記錄每次解析的 metadata。連線資訊從環境變數讀取。

#### Scenario: Insert new import record
- **WHEN** 完成一次 recipe body 解析
- **THEN** 寫入一筆記錄，包含 machine_type、machine_id、product_type、bop、wafer_pn、recipe_version、recipe_name、mc_serial、sw_version、recipe_datetime、lot_id（可為 NULL）、source_file、import_datetime

#### Scenario: Database connection from environment variables
- **WHEN** pipeline 服務啟動並初始化資料庫連線
- **THEN** 系統從 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`、`MYSQL_CHARSET` 環境變數建立 SQLAlchemy 連線，不再從 config.yaml 讀取
