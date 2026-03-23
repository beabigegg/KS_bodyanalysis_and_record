## ADDED Requirements

### Requirement: Browse recipe import records
系統 SHALL 提供 recipe import 記錄列表頁面，顯示所有已解析的 recipe body 記錄。

#### Scenario: View import list with filters
- **WHEN** 使用者進入參數瀏覽頁面
- **THEN** 系統顯示 ksbody_recipe_import 記錄列表，包含 machine_type、machine_id、product_type、bop、wafer_pn、recipe_datetime、import_datetime，支援分頁

#### Scenario: Filter by machine and product
- **WHEN** 使用者選擇 machine_type、machine_id、product_type 任意組合篩選
- **THEN** 系統 SHALL 即時篩選並顯示符合條件的記錄

#### Scenario: Search by keyword
- **WHEN** 使用者輸入關鍵字搜尋
- **THEN** 系統 SHALL 在 product_type、bop、wafer_pn、recipe_name 欄位中模糊搜尋

### Requirement: View recipe parameters detail
系統 SHALL 提供單筆 recipe import 的參數詳細檢視頁面。

#### Scenario: View all parameters grouped by file type
- **WHEN** 使用者點選某筆 import 記錄
- **THEN** 系統顯示該 recipe 的所有參數，依 file_type 分組（PRM、PHY、BND 等），每組顯示 param_name、param_value、unit、min_value、max_value、default_value

#### Scenario: Filter parameters by name
- **WHEN** 使用者在參數詳細頁輸入參數名稱篩選
- **THEN** 系統 SHALL 即時篩選顯示匹配的參數列

#### Scenario: View APP spec details
- **WHEN** 使用者切換到 APP 分頁
- **THEN** 系統顯示 ksbody_recipe_app_spec 的耗材規格（Capillary、Wire 資訊）

#### Scenario: View BSG details
- **WHEN** 使用者切換到 BSG 分頁
- **THEN** 系統顯示 ksbody_recipe_bsg 的 Ball Signature 檢測參數，依 ball_group 分組

#### Scenario: View RPM data
- **WHEN** 使用者切換到 RPM 分頁
- **THEN** 系統顯示 ksbody_recipe_rpm_limits 和 ksbody_recipe_rpm_reference 資料

### Requirement: Export parameters
系統 SHALL 支援將參數資料匯出為 CSV 檔案。

#### Scenario: Export filtered parameters
- **WHEN** 使用者在參數詳細頁點選「匯出 CSV」
- **THEN** 系統 SHALL 下載目前篩選/顯示的參數為 CSV 檔案
