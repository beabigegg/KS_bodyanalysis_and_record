## ADDED Requirements

### Requirement: Select recipes for comparison
系統 SHALL 允許使用者選擇兩筆或多筆不同機台的 recipe import 記錄進行比較。

#### Scenario: Select comparison targets
- **WHEN** 使用者指定 product_type + bop + wafer_pn
- **THEN** 系統列出所有符合條件的機台（machine_id）及其最新 recipe import 記錄，供使用者勾選比較對象

#### Scenario: Quick compare latest recipes
- **WHEN** 使用者選定產品後點選「比較所有機台」
- **THEN** 系統 SHALL 自動選取每台機器該產品的最新 recipe import 進行比較

### Requirement: Display parameter differences
系統 SHALL 以 Diff 視圖顯示被比較 recipe 之間的參數差異。

#### Scenario: Show only differences
- **WHEN** 比較結果產生
- **THEN** 系統預設僅顯示有差異的參數，以高亮標示不同的值

#### Scenario: Show all parameters
- **WHEN** 使用者切換「顯示全部參數」
- **THEN** 系統顯示所有參數，差異行仍然高亮標示

#### Scenario: Filter differences by file type
- **WHEN** 使用者選擇特定 file_type（如 PRM）
- **THEN** 系統 SHALL 僅顯示該 file_type 的比較結果

### Requirement: Compare APP and BSG wide tables
系統 SHALL 支援 recipe_app_spec 和 recipe_bsg 寬表的跨機台比較。

#### Scenario: Compare capillary and wire specs
- **WHEN** 比較包含 APP 資料
- **THEN** 系統 SHALL 並列顯示各機台的耗材規格，差異值高亮

#### Scenario: Compare ball signature settings
- **WHEN** 比較包含 BSG 資料
- **THEN** 系統 SHALL 並列顯示各機台的 Ball Signature 設定，差異值高亮
