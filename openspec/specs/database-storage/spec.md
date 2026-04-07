## ADDED Requirements

### Requirement: Create recipe_import master table
系統 SHALL 在 MySQL 建立 recipe_import 主表，記錄每次解析的 metadata。連線資訊從環境變數讀取。

#### Scenario: Insert new import record
- **WHEN** 完成一次 recipe body 解析
- **THEN** 寫入一筆記錄，包含 machine_type、machine_id、product_type、bop、wafer_pn、recipe_version、recipe_name、mc_serial、sw_version、recipe_datetime、lot_id（可為 NULL）、source_file、import_datetime

#### Scenario: Database connection from environment variables
- **WHEN** pipeline 服務啟動並初始化資料庫連線
- **THEN** 系統從 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`、`MYSQL_CHARSET` 環境變數建立 SQLAlchemy 連線，不再從 config.yaml 讀取

#### Scenario: Duplicate file parsed again
- **WHEN** 同一檔案被覆蓋更新後再次解析
- **THEN** 系統 SHALL 建立新的 import 記錄（新的 id 和 import_datetime），保留歷史記錄

### Requirement: Create recipe_params EAV table
系統 SHALL 建立 recipe_params 表，以 Entity-Attribute-Value 模式儲存所有解析出的參數。

#### Scenario: Bulk insert parameters
- **WHEN** 從 PRM 檔解析出數百個參數
- **THEN** 批量寫入 recipe_params，每筆包含 recipe_import_id (FK)、file_type、param_name、param_value、unit、min_value、max_value、default_value

#### Scenario: Query parameters for cross-machine comparison
- **WHEN** 查詢同一 product_type + bop + wafer_pn 在不同 machine_id 的特定參數
- **THEN** 系統的資料模型 SHALL 支援以 (product_type, bop, wafer_pn, param_name) 為條件的高效查詢

### Requirement: Create recipe_app_spec wide table
系統 SHALL 建立 recipe_app_spec 寬表，儲存 APP 檔案中的耗材規格。

#### Scenario: Insert capillary and wire specs
- **WHEN** 解析完 APP 檔案
- **THEN** 寫入一筆記錄，包含 recipe_import_id、cap_manufacturer、cap_part_number、cap_tip_dia、cap_hole_dia、chamfer_dia、inner_cone_angle、face_angle、wire_manufacturer、wire_part_number、wire_dia、wire_metal

### Requirement: Create recipe_bsg table
系統 SHALL 建立 recipe_bsg 表，儲存 Ball Signature 檢測參數。

#### Scenario: Insert ball signature data
- **WHEN** 解析完 BSG 檔案
- **THEN** 為每個 ball_group 寫入一筆記錄，包含 inspection 和 process 相關參數

### Requirement: Create recipe_rpm_limits table
系統 SHALL 建立 recipe_rpm_limits 表，儲存從 RPM SQLite 搬入的限值資料。

#### Scenario: Insert RPM limits
- **WHEN** 從 RPM SQLite 提取 limits 資料
- **THEN** 批量寫入，每筆包含 recipe_import_id、signal_name、property_name、rpm_group、bond_type、measurement_name、limit_type、statistic_type、parameter_set、lower_limit、upper_limit、active

### Requirement: Create recipe_rpm_reference table
系統 SHALL 建立 recipe_rpm_reference 表，儲存 RPM 統計參考資料。

#### Scenario: Insert RPM reference data
- **WHEN** 從 RPM SQLite 提取 reference data
- **THEN** 批量寫入，每筆包含 recipe_import_id、signal_name、property_name、rpm_group、bond_type、measurement_name、source、average、median、std_dev、median_abs_dev、minimum、maximum、sample_count

### Requirement: Index design for query performance
系統 SHALL 在關鍵查詢欄位建立索引，支援跨機台比較和時間序列查詢。

#### Scenario: Cross-machine query performance
- **WHEN** 查詢同產品跨機台的參數比較
- **THEN** recipe_import 表 SHALL 在 (product_type, bop, wafer_pn, machine_id) 上有複合索引

#### Scenario: Time-series query performance
- **WHEN** 查詢同機台同產品的歷史參數變化
- **THEN** recipe_import 表 SHALL 在 (machine_id, product_type, recipe_datetime) 上有複合索引

#### Scenario: Parameter lookup performance
- **WHEN** 查詢特定參數名稱的值
- **THEN** recipe_params 表 SHALL 在 (recipe_import_id, file_type, param_name) 上有複合索引

### Requirement: Transaction integrity
系統 SHALL 確保每次解析的所有資料在同一個 transaction 中寫入。

#### Scenario: Partial failure rollback
- **WHEN** 寫入過程中某張表 insert 失敗
- **THEN** 系統 SHALL rollback 整個 transaction，不留下部分資料
