## 1. 專案結構與配置

- [x] 1.1 建立 web/backend/ 和 web/frontend/ 目錄結構
- [x] 1.2 建立 .env.example 範本（APP_PORT、APP_MODE、MySQL 連線、Oracle 連線預留）
- [x] 1.3 建立 web/backend/requirements.txt（fastapi, uvicorn, python-dotenv, sqlalchemy, pymysql）
- [x] 1.4 建立 web/backend/config.py，使用 python-dotenv 載入 .env 配置
- [x] 1.5 使用 Vite 初始化 React + TypeScript 前端專案（web/frontend/）
- [x] 1.6 安裝前端依賴：tailwindcss、shadcn/ui、recharts、axios

## 2. 後端 API 基礎

- [x] 2.1 建立 web/backend/app.py FastAPI 入口，含 CORS 設定和靜態檔案託管邏輯
- [x] 2.2 建立 web/backend/deps.py，建立 SQLAlchemy engine（import 現有 db/schema.py）
- [x] 2.3 建立 web/backend/api/imports.py，實作 GET /api/imports（篩選、分頁、搜尋）
- [x] 2.4 建立 web/backend/api/imports.py，實作 GET /api/imports/{id}/params（依 file_type 分組）
- [x] 2.5 建立 web/backend/api/imports.py，實作 GET /api/imports/{id}/app-spec 和 /bsg 和 /rpm

## 3. 參數瀏覽前端

- [x] 3.1 建立前端路由結構和導航佈局（側邊欄 + 主內容區）
- [x] 3.2 建立 ImportListPage：recipe import 記錄列表，含篩選器（machine_type、machine_id、product_type 下拉選單）和搜尋框
- [x] 3.3 建立 ImportDetailPage：參數詳細檢視，file_type 分頁切換，參數表格含搜尋篩選
- [x] 3.4 建立 APP/BSG/RPM 分頁組件，顯示寬表資料
- [x] 3.5 實作 CSV 匯出功能（前端組裝 CSV 下載）

## 4. 跨機台比較

- [x] 4.1 建立 web/backend/api/compare.py，實作 POST /api/compare（接收多個 import_id，回傳參數 Diff）
- [x] 4.2 建立 ComparePage：產品選擇 → 機台列表勾選 → 觸發比較
- [x] 4.3 建立 DiffTable 組件：並列顯示各機台參數值，差異高亮，支援「僅顯示差異/顯示全部」切換
- [x] 4.4 建立 APP/BSG 寬表比較視圖

## 5. 時間趨勢分析

- [x] 5.1 建立 web/backend/api/trend.py，實作 GET /api/trend（machine_id、product_type、param_name、時間範圍）
- [x] 5.2 建立 TrendPage：機台/產品/參數選擇器 + 時間範圍篩選
- [x] 5.3 建立 TrendChart 組件：Recharts 折線圖，含 min/max/default 參考線、hover tooltip
- [x] 5.4 實作多參數疊加和多機台對比模式

## 6. R2R 事後分析

- [x] 6.1 建立 web/backend/api/r2r.py，實作 GET /api/r2r/stats（計算 mean、std_dev、UCL、LCL、Cp、Cpk）
- [x] 6.2 建立 R2RPage：機台/產品選擇 → 關鍵參數管制狀態摘要儀表板
- [x] 6.3 建立 ControlChart 組件：Xbar 管制圖，含 CL/UCL/LCL 線和超限點紅色標示
- [x] 6.4 建立 DistributionChart 組件：直方圖 + 常態分佈曲線 + 規格界限
- [x] 6.5 實作參數觀察清單功能（localStorage 持久化）

## 7. 良率對照（預留）

- [x] 7.1 建立 web/backend/services/oracle_conn.py，Oracle 連線模組（.env 配置，未配置時 graceful skip）
- [x] 7.2 建立 web/backend/api/yield_corr.py，實作良率查詢和時間匹配端點
- [x] 7.3 建立 YieldCorrelationPage：雙 Y 軸趨勢圖（參數 + 良率）和散點圖（相關性分析）
- [x] 7.4 未配置 Oracle 時顯示「尚未配置」提示頁面

## 8. 整合與部署

- [x] 8.1 前端 build 後由 FastAPI 託管靜態檔案，驗證 prod 模式單一服務運行
- [x] 8.2 建立啟動腳本 start.sh / start.bat（conda activate + uvicorn 啟動）
- [x] 8.3 端對端測試：使用現有 MySQL 資料驗證所有頁面功能
