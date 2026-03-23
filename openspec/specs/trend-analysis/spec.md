## ADDED Requirements

### Requirement: Select parameters for trend tracking
系統 SHALL 允許使用者選擇特定機台、產品和參數名稱，查看該參數隨時間的變化趨勢。

#### Scenario: Select trend target
- **WHEN** 使用者指定 machine_id + product_type + bop + wafer_pn + param_name
- **THEN** 系統查詢所有歷史 recipe import 中該參數的值，按 recipe_datetime 排序

#### Scenario: Multiple parameters overlay
- **WHEN** 使用者選擇多個 param_name
- **THEN** 系統 SHALL 在同一圖表上以不同顏色線條疊加顯示各參數的趨勢

### Requirement: Display trend chart
系統 SHALL 以折線圖顯示參數值隨時間的變化趨勢。

#### Scenario: Render time-series line chart
- **WHEN** 查詢結果回傳
- **THEN** 系統顯示折線圖，X 軸為 recipe_datetime，Y 軸為 param_value，每個資料點可 hover 顯示完整資訊

#### Scenario: Show min/max/default reference lines
- **WHEN** 參數有 min_value、max_value、default_value
- **THEN** 系統 SHALL 在圖表上顯示水平參考線標示規格上下限和預設值

#### Scenario: Time range filter
- **WHEN** 使用者選擇時間範圍（如最近 30 天、90 天、自訂）
- **THEN** 系統 SHALL 僅顯示該時間範圍內的資料點

### Requirement: Cross-machine trend comparison
系統 SHALL 支援同一參數在不同機台之間的趨勢對比。

#### Scenario: Overlay multiple machines
- **WHEN** 使用者選擇同產品的多台機器和同一參數
- **THEN** 系統 SHALL 在同一圖表上以不同顏色顯示各機台的趨勢線
