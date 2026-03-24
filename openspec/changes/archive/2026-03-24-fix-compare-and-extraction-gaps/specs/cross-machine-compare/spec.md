## MODIFIED Requirements

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

#### Scenario: Parameter exists on one machine but not another
- **WHEN** 某參數僅存在於部分機台的 recipe 中（其餘機台該參數為 null）
- **THEN** 系統 SHALL 將此情況標記為差異（`is_diff = true`）並顯示於結果中
- **AND** 缺少該參數的機台 SHALL 顯示為空值（null / —）

#### Scenario: BSG params excluded from params section
- **WHEN** 比較結果的 params 區段產生
- **THEN** 系統 SHALL 排除 `file_type = 'BSG'` 的參數，這些資料已由獨立的 BSG Diff 區塊呈現

## ADDED Requirements

### Requirement: Include RPM data in comparison
系統 SHALL 在跨機台比較結果中包含 RPM 資料區塊，詳見 `rpm-comparison` spec。

#### Scenario: RPM sections present in compare response
- **WHEN** 比較請求成功完成
- **THEN** API 回傳的 `data` 物件 SHALL 包含 `rpm_limits` 和 `rpm_reference` 兩個區段
