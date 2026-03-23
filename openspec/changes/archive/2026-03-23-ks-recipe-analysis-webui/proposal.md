## Why

後端解析引擎已完成，MySQL 中累積了 5,000+ 筆結構化 recipe 參數（ksbody_ 表群），但目前缺乏視覺化介面供工程師瀏覽、比較和分析資料。生產端需要快速識別跨機台參數差異、追蹤參數隨時間的變化趨勢、並將 recipe 參數與最終測試良率對照，以找出影響製程品質的關鍵參數。

## What Changes

- 建立 FastAPI 後端 API，提供 recipe 參數查詢、跨機台比較、時間趨勢和統計分析端點
- 建立 Vite + React 前端，包含參數瀏覽、跨機台比較、時間趨勢圖表、良率對照和 R2R 事後分析五大功能模組
- 使用 .env 檔案管理 port、執行模式、認證和資料庫連線設定
- 後端連接現有 MySQL (ksbody_) 資料庫讀取 recipe 資料
- 預留 Oracle 連線接口，供良率資料對照使用
- 部署目標為 Conda 環境，未來移植至 Linux (1Panel)

## Capabilities

### New Capabilities
- `param-browser`: 參數瀏覽功能，支援依機台/產品/檔案類型篩選、搜尋和匯出 recipe 參數
- `cross-machine-compare`: 跨機台比較功能，同產品不同機台的參數差異 Diff 高亮顯示
- `trend-analysis`: 時間趨勢分析，同機台同產品的參數歷史變化圖表
- `yield-correlation`: 良率對照功能，將 Oracle 測試良率資料與 recipe 參數對照分析
- `r2r-analysis`: Run-to-Run 事後分析，SPC 統計圖表和參數穩定性監控
- `webui-backend`: FastAPI 後端 API 層，提供所有分析功能的 REST 端點和 .env 配置管理

### Modified Capabilities

(無既有 spec 需修改)

## Impact

- **新增依賴 (Backend)**: fastapi, uvicorn, python-dotenv, cx_Oracle/oracledb (Phase 後期)
- **新增依賴 (Frontend)**: vite, react, recharts/echarts, tailwindcss, shadcn/ui
- **資料庫**: 唯讀存取現有 MySQL ksbody_ 表群，新增 Oracle 唯讀連線 (良率)
- **網路**: WebUI 服務端口由 .env 配置，預設使用 12010-12019 區間
- **部署**: Conda 環境運行，未來遷移至 Linux 1Panel
- **現有系統**: 不影響現有的 watcher/parser 背景服務
