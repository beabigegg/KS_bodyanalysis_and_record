## ADDED Requirements

### Requirement: Compare RPM limits across machines
系統 SHALL 在跨機台比較中包含 recipe_rpm_limits 的差異比對。

#### Scenario: RPM limits diff shown in compare result
- **WHEN** 使用者提交跨機台比較請求
- **THEN** 回傳結果 SHALL 包含 `rpm_limits` 區段，列出所有 (signal_name, property_name, rpm_group, bond_type, measurement_name, limit_type, statistic_type, parameter_set) 組合的差異
- **AND** 每筆記錄 SHALL 呈現各機台的 `lower_limit`、`upper_limit`、`active` 值
- **AND** 預設僅顯示有差異的記錄（`show_all=False`）

#### Scenario: RPM limits absent for one machine
- **WHEN** 某台機器的 import 沒有 RPM 資料
- **THEN** 該機台的 RPM limits 欄位 SHALL 以 `null` 表示
- **AND** 「一方有值、另一方為 null」SHALL 被標記為差異（`is_diff = true`）

#### Scenario: Filter RPM limits by show_all
- **WHEN** 使用者設定 `show_all=true`
- **THEN** 系統 SHALL 顯示所有 RPM limits 記錄，無論是否有差異

### Requirement: Compare RPM reference statistics across machines
系統 SHALL 在跨機台比較中包含 recipe_rpm_reference 的統計值差異比對。

#### Scenario: RPM reference diff shown in compare result
- **WHEN** 使用者提交跨機台比較請求
- **THEN** 回傳結果 SHALL 包含 `rpm_reference` 區段，列出所有 (signal_name, property_name, rpm_group, bond_type, measurement_name, source) 組合的差異
- **AND** 每筆記錄 SHALL 呈現各機台的 `average`、`median`、`std_dev`、`median_abs_dev`、`minimum`、`maximum`、`sample_count` 值

#### Scenario: RPM reference absent for one machine
- **WHEN** 某台機器的 import 沒有 RPM reference 資料
- **THEN** 該機台的所有統計欄位 SHALL 以 `null` 表示
- **AND** 「一方有統計值、另一方全 null」SHALL 被標記為差異

### Requirement: Display RPM comparison in frontend
系統前端 SHALL 在跨機台比較頁面呈現 RPM 比較結果。

#### Scenario: RPM Limits Diff section displayed
- **WHEN** 比較結果含有 `rpm_limits` 資料
- **THEN** 前端 SHALL 在 BSG Diff 之後顯示 RPM Limits Diff 區塊
- **AND** 使用與其他 Diff 區塊一致的表格格式（有差異行高亮）

#### Scenario: RPM Reference Diff section displayed
- **WHEN** 比較結果含有 `rpm_reference` 資料
- **THEN** 前端 SHALL 在 RPM Limits Diff 之後顯示 RPM Reference Diff 區塊
