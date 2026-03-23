## Context

KS ConnX Elite 打線機的 recipe body 解析引擎已完成，MySQL 中有 6 張 ksbody_ 表儲存結構化參數資料。現在需要建立 WebUI 分析平台，讓工程師能瀏覽參數、比較機台差異、追蹤趨勢和對照良率。

現有後端模組（parsers、db、watcher）為背景服務，WebUI 作為獨立的 FastAPI + Vite/React 應用，唯讀存取同一個 MySQL 資料庫。

部署環境為 Windows Conda，未來遷移至 Linux 1Panel。所有可配置項（port、DB 連線、認證）由 .env 管理。

## Goals / Non-Goals

**Goals:**
- 提供 WebUI 介面瀏覽所有已解析的 recipe 參數
- 支援跨機台同產品的參數差異比較（Diff 高亮）
- 提供時間趨勢圖表，追蹤參數隨時間的變化
- 預留 Oracle 良率資料對照接口
- 提供 R2R 事後分析的 SPC 統計圖表
- 所有配置透過 .env 管理，便於環境遷移

**Non-Goals:**
- Recipe 參數修改/回寫/Fanout（另一個專案）
- 即時推送/WebSocket
- 使用者權限分級管理（本階段不鎖認證或僅基礎認證）
- Docker 部署

## Decisions

### 1. 單體式架構（IT 規範）

**約束**: IT 要求應用程式為單體式架構，所有前端頁面由後端統一伺服，單一應用僅佔用一個 Port。

**選擇**: FastAPI 統一伺服 API + 靜態檔案，前端使用 Vite/React 開發後 build 產出靜態檔案

**部署模式**:
```
FastAPI (單一 port)
├─ /api/*  → REST API 路由
└─ /*      → 伺服 frontend/dist/ 靜態檔案（React SPA）
```

**開發模式**: Vite dev server 搭配 proxy 設定，將 /api 請求轉發到本機 FastAPI，開發完成後 `vite build` 產出靜態檔案供 FastAPI 託管

**替代方案**: Streamlit、Jinja2 SSR

**理由**:
- 符合 IT 單體式部署規範，單一 port 運行
- 功能複雜度高（互動表格、Diff、圖表），需要完整前端框架
- Vite 開發體驗好（HMR），React 生態成熟
- 不需要 Nginx 或額外反向代理

### 2. 前端 UI 框架：Tailwind + shadcn/ui

**選擇**: Tailwind CSS + shadcn/ui 組件庫

**替代方案**: Ant Design、Material UI

**理由**:
- shadcn/ui 是 copy-paste 模式，不增加 node_modules 體積
- Tailwind 的 utility-first 適合快速疊代
- 輕量，適合工具型應用

### 3. 圖表庫：Recharts

**選擇**: Recharts

**替代方案**: ECharts、Chart.js、Plotly

**理由**:
- React 原生組件化 API，與 React 整合最自然
- 支援折線圖（趨勢）、散點圖（良率相關性）、直方圖（分佈）
- 輕量，學習曲線低
- SPC 圖（管制圖）可用折線圖 + 參考線實現

### 4. 資料庫存取策略

**選擇**: 唯讀存取現有 ksbody_ 表群，不新增資料表

**理由**:
- 分析平台為純查詢，不需要寫入
- 共用 SQLAlchemy schema 定義（從現有 db/schema.py import）
- 避免表結構耦合

### 5. Oracle 良率資料接口

**選擇**: 預留 oracledb 連線模組，Phase 後期接入

**理由**:
- 良率資料來源為 Oracle，目前連線細節待確認
- 先建好 API 端點和前端 UI 框架，Oracle 接入作為獨立模組插入
- 使用 .env 配置 Oracle 連線，不接入時功能隱藏或顯示「尚未配置」

### 6. 配置管理：.env

**選擇**: python-dotenv 載入 .env 檔案

**理由**:
- 統一管理 port、debug mode、MySQL/Oracle 連線、認證設定
- .env 加入 .gitignore，提供 .env.example 範本
- 1Panel 部署時直接修改 .env 即可

### 7. 專案目錄結構

```
web/
├── backend/
│   ├── api/              # FastAPI 路由
│   │   ├── params.py     # 參數瀏覽
│   │   ├── compare.py    # 跨機台比較
│   │   ├── trend.py      # 時間趨勢
│   │   ├── yield_corr.py # 良率對照
│   │   └── r2r.py        # R2R 分析
│   ├── services/         # 業務邏輯
│   ├── app.py            # FastAPI 入口
│   └── deps.py           # 依賴注入（DB engine）
├── frontend/
│   ├── src/
│   │   ├── components/   # 共用組件
│   │   ├── pages/        # 頁面
│   │   ├── hooks/        # API hooks
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── .env.example
└── requirements.txt
```

## Risks / Trade-offs

- **跨機台比較的資料量** → 兩台機器的 PRM 各有 ~2000 參數，Diff 計算可能慢。Mitigation: 後端做 Diff，只回傳有差異的參數，前端分頁載入。
- **Oracle 連線不確定性** → 連線方式、表結構、權限都待確認。Mitigation: 良率模組設計為可拔插，不影響其他功能。
- **圖表效能** → 長時間範圍的趨勢圖可能有大量資料點。Mitigation: 後端做時間聚合（日/週），限制回傳筆數。
- **Conda → Linux 遷移** → Windows 路徑和 Linux 路徑不同。Mitigation: 所有路徑配置在 .env 中，不寫死。

## Open Questions

- Oracle 良率資料的連線方式和表結構？
- R2R 分析需要哪些具體的 SPC 圖表？（Xbar-R？Cp/Cpk？）
- 是否需要匯出功能（CSV/Excel）？
- 認證機制：完全不鎖？還是基礎的 .env 密碼保護？
