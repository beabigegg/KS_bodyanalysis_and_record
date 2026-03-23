## ADDED Requirements

### Requirement: SPC control chart
系統 SHALL 提供 SPC 管制圖，對選定參數進行統計過程控制分析。

#### Scenario: Render Xbar control chart
- **WHEN** 使用者選擇特定機台、產品和參數進行 R2R 分析
- **THEN** 系統 SHALL 顯示 Xbar 管制圖，包含中心線（CL）、管制上限（UCL）和管制下限（LCL）

#### Scenario: Highlight out-of-control points
- **WHEN** 管制圖中有超出 UCL/LCL 的資料點
- **THEN** 系統 SHALL 以紅色標示超出管制界限的資料點

### Requirement: Parameter stability analysis
系統 SHALL 計算並顯示參數的穩定性統計指標。

#### Scenario: Display statistical summary
- **WHEN** 使用者選擇參數進行分析
- **THEN** 系統 SHALL 顯示 mean、std_dev、Cp、Cpk（若有規格上下限）、資料點數量

#### Scenario: Distribution histogram
- **WHEN** 使用者切換到「分佈」分頁
- **THEN** 系統 SHALL 以直方圖顯示參數值分佈，疊加常態分佈曲線和規格界限

### Requirement: Multi-parameter R2R dashboard
系統 SHALL 提供多參數 R2R 總覽儀表板。

#### Scenario: Dashboard overview
- **WHEN** 使用者選擇機台和產品進入 R2R 儀表板
- **THEN** 系統 SHALL 顯示關鍵參數的管制狀態摘要（正常/警告/異常），點選可展開詳細管制圖

#### Scenario: Custom parameter watchlist
- **WHEN** 使用者將特定參數加入觀察清單
- **THEN** 系統 SHALL 在儀表板優先顯示觀察清單中的參數狀態
