# KS Recipe Analysis WebUI

KS ConnX Elite 打線機 recipe 參數分析平台。唯讀存取 MySQL 中的 `ksbody_` 表群，提供參數瀏覽、跨機台比較、時間趨勢、R2R SPC 分析及良率對照功能。

## 系統架構

單體式（Monolithic）架構，FastAPI 同時伺服 REST API 和前端靜態檔案，僅佔用單一 Port。

```
FastAPI (single port)
├─ /api/*      → REST API 路由
├─ /api/health → 健康檢查端點
└─ /*          → 前端靜態檔案 (React SPA)
```

### 技術選型

- **後端**: Python 3.11 + FastAPI + SQLAlchemy (read-only)
- **前端**: React + TypeScript + Vite + Tailwind CSS + shadcn/ui + Recharts
- **資料庫**: MySQL (ksbody_ 表群) + Oracle (良率，選用)
- **環境管理**: Conda

## 安裝方式

```bash
# 1. 安裝後端依賴
cd web/
conda activate ksbody
pip install -r requirements.txt

# 2. 安裝前端依賴並建置
cd frontend/
npm install
npm run build
cd ..
```

## 環境變數說明

複製 `.env.example` 為 `.env` 並填入實際值：

```bash
cp .env.example .env
```

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `APP_PORT` | 監聽端口 | `12010` |
| `APP_HOST` | 綁定位址 | `0.0.0.0` |
| `APP_MODE` | 環境模式 (dev/prod) | `dev` |
| `APP_DEBUG` | 除錯模式 (正式環境禁止 true) | `false` |
| `APP_CORS_ORIGINS` | CORS 來源清單，逗號分隔 | `http://localhost:5173` |
| `MYSQL_HOST` | MySQL 主機 | `127.0.0.1` |
| `MYSQL_PORT` | MySQL 端口 | `3306` |
| `MYSQL_USER` | MySQL 使用者 | `root` |
| `MYSQL_PASSWORD` | MySQL 密碼 | - |
| `MYSQL_DATABASE` | MySQL 資料庫名稱 | - |
| `ORACLE_DSN` | Oracle DSN (選用) | - |
| `ORACLE_USER` | Oracle 使用者 (選用) | - |
| `ORACLE_PASSWORD` | Oracle 密碼 (選用) | - |

## 啟動指令

```bash
cd web/
python app.py
```

或使用啟動腳本：
- Windows: `start.bat`
- Linux: `./start.sh`

## 使用方式

啟動後瀏覽器開啟 `http://localhost:12010`，功能包含：

- **Import Records** — 瀏覽已解析的 recipe import 記錄，篩選/搜尋/CSV 匯出
- **Cross-Machine Compare** — 跨機台同產品參數差異比較，Diff 高亮
- **Trend Analysis** — 參數時間趨勢折線圖，支援多機台/多參數疊加
- **R2R SPC Dashboard** — Xbar 管制圖、Cp/Cpk、分佈直方圖、觀察清單
- **Yield Correlation** — 良率對照（需配置 Oracle 連線）

## 部署說明

### 正式環境

1. `.env` 設定 `APP_MODE=prod`、`APP_DEBUG=false`
2. 前端建置：`cd frontend && npm run build`
3. 啟動：`python app.py`（FastAPI 託管 `frontend/dist/` 靜態檔案）
4. 單一 Port 運行，無需 Nginx 反向代理

### 開發環境

1. `.env` 設定 `APP_MODE=dev`
2. 後端：`python app.py`（自動 reload）
3. 前端：`cd frontend && npm run dev`（Vite dev server，proxy `/api` 到後端）
