## MODIFIED Requirements

### Requirement: Display parameter differences
系統 SHALL 以 Diff 視圖顯示被比較 recipe 之間的參數差異，並依製程階段（stage）和功能域（category）分組呈現。

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

#### Scenario: Param rows include stage and category
- **WHEN** Compare API 回傳 params 區段
- **THEN** 每筆 param row SHALL 包含 `stage`（字串或 null）和 `category`（字串或 null）欄位
- **AND** 這兩個欄位由 `ParamClassifier` 根據 `param_name` 和 `file_type` 計算

#### Scenario: Parameters grouped by stage and category in UI
- **WHEN** 前端渲染 Parameter Diff 區塊
- **THEN** 系統 SHALL 依 `stage` → `category` 兩層折疊分組顯示參數
- **AND** 每個 stage 群組顯示其下的 diff 數量
- **AND** 預設展開有差異的 stage 群組

#### Scenario: Unclassified params displayed under _unmapped
- **WHEN** 某筆 param row 的 `stage = "_unmapped"`
- **THEN** 系統 SHALL 將其歸入「未分類」區塊，不隱藏
