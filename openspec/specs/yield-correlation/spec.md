## ADDED Requirements

### Requirement: Oracle yield data connection
系統 SHALL 支援從 Oracle 資料庫讀取最終測試良率資料，連線配置由 .env 管理。

#### Scenario: Oracle connection configured
- **WHEN** .env 中配置了 Oracle 連線資訊
- **THEN** 系統啟動時建立 Oracle 唯讀連線，良率對照功能可用

#### Scenario: Oracle connection not configured
- **WHEN** .env 中未配置 Oracle 連線
- **THEN** 系統 SHALL 在良率對照頁面顯示「Oracle 連線尚未配置」提示，其他功能不受影響

### Requirement: Yield vs parameter correlation view
系統 SHALL 提供良率與 recipe 參數的對照分析介面。

#### Scenario: Display yield trend alongside parameter trend
- **WHEN** 使用者選擇特定機台、產品和參數
- **THEN** 系統 SHALL 在雙 Y 軸圖表上同時顯示參數值趨勢和對應時段的良率趨勢

#### Scenario: Scatter plot for correlation analysis
- **WHEN** 使用者選擇「相關性分析」模式
- **THEN** 系統 SHALL 以散點圖顯示參數值（X 軸）vs 良率（Y 軸），協助識別參數與良率的關聯

### Requirement: Yield data matching
系統 SHALL 將 Oracle 良率資料與 recipe import 記錄進行時間匹配。

#### Scenario: Match by time window
- **WHEN** 進行良率對照
- **THEN** 系統 SHALL 根據 recipe_datetime 和良率測試時間進行時間窗口匹配，將 recipe 參數與相應的良率資料關聯
