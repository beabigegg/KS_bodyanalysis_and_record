# KS Body Analysis and Record

自動監控 SMB 網路資料夾，解析 recipe body 檔案並寫入資料庫，同時提供 Web API 供查詢。

## 目錄

- [專案功能](#專案功能)
- [技術棧](#技術棧)
- [專案結構](#專案結構)
- [環境需求](#環境需求)
- [快速開始](#快速開始)
- [設定說明](#設定說明)
- [部署](#部署)
- [啟動與管理](#啟動與管理)
- [CLI 指令](#cli-指令)
- [異常排除](#異常排除)

---

## 專案功能

| 模組 | 說明 |
|------|------|
| **Folder Watcher** | 遞迴監控指定目錄，偵測新增或修改的 recipe body 檔案 |
| **Pipeline** | 解析 recipe body 檔案內容並寫入 MySQL |
| **Scanner** | 定時掃描（預設每 5 分鐘），補抓 watcher 遺漏的檔案 |
| **Web API** | FastAPI + uvicorn 提供 REST API，供前端查詢分析結果 |
| **Frontend** | React 前端，打包後由 FastAPI 靜態服務 |

**典型部署情境：** 機台將 recipe body 寫入 SMB 共享資料夾 → Linux 主機掛載該 SMB share → Watcher 偵測到新檔案 → Pipeline 解析寫庫 → Web 呈現結果。

---

## 技術棧

**後端**
- Python 3.11+
- FastAPI + uvicorn
- SQLAlchemy 2.0 + PyMySQL
- watchdog（PollingObserver，支援 SMB 掛載路徑）
- python-dotenv

**前端**
- React + React Router + Redux
- Vite + TypeScript + Tailwind CSS

**資料庫**
- MySQL（必要）
- Oracle（選用）

**系統依賴**
- `cifs-utils`：SMB 掛載（`mount.cifs`）

---

## 專案結構

```
.
├── ksbody/                  # 主套件
│   ├── watcher/             # Folder watcher（observer、handler、scanner）
│   ├── pipeline/            # 解析與寫庫邏輯
│   ├── web/                 # FastAPI app 與前端
│   │   └── frontend/        # React 前端原始碼
│   ├── db/                  # 資料庫 model 與初始化
│   ├── config.py            # 統一設定（從 .env 讀取）
│   └── __main__.py          # CLI 入口
├── scripts/
│   ├── deploy.sh            # 一鍵部署（Python + 前端，自動呼叫 mount-smb.sh）
│   ├── mount-smb.sh         # SMB 掛載（需 sudo，deploy.sh 自動呼叫）
│   └── start.sh             # 服務管理（start / stop / restart / status）
├── tests/
├── pyproject.toml
├── .env                     # 執行期設定（不進 git）
└── .env.example             # 設定範本
```

---

## 環境需求

- Linux（Ubuntu 20.04+）
- Python 3.11+（建議透過 conda 管理）
- Node.js 18+（前端打包）
- MySQL 8.0+
- `cifs-utils`（SMB 掛載）

安裝系統依賴：

```bash
sudo apt install cifs-utils
```

---

## 快速開始

```bash
# 1. 複製設定範本
cp .env.example .env
# 編輯 .env，填入 MySQL、SMB 認證、WATCH_PATHS

# 2. 執行部署（會自動掛載 SMB、安裝 Python 套件、打包前端）
./scripts/deploy.sh

# 3. 啟動服務
./scripts/start.sh start

# 4. 確認服務正常
curl http://127.0.0.1:12010/api/health
```

---

## 設定說明

複製 `.env.example` 為 `.env` 並填入以下設定：

### MySQL

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=change-me
MYSQL_DATABASE=ksbody_analysis
```

### 監控路徑（SMB 掛載後的本地路徑）

```env
WATCH_PATHS=/mnt/eap_recipe/WBK_ConnX Elite
```

> 多個路徑以逗號分隔：`WATCH_PATHS=/mnt/share1,/mnt/share2`
>
> **注意：** 必須使用 Linux 本地掛載路徑，不可直接使用 Windows UNC 路徑（`\\server\share`），原因見[部署 - SMB 掛載](#smb-掛載)。

### SMB 認證（供 deploy.sh 自動掛載使用）

```env
RECIPE_TRACE_SMB_HOST=<SMB_SERVER_IP>
RECIPE_TRACE_SMB_SHARE=<SHARE_NAME>
RECIPE_TRACE_SMB_USER=<SMB_USERNAME>
RECIPE_TRACE_SMB_PASSWORD=change-me
```

### Pipeline 調校

```env
DEBOUNCE_SETTLE_SECONDS=5   # 等待檔案寫入穩定的秒數
DEBOUNCE_POLL_SECONDS=1     # 檢查穩定的輪詢間隔
DEBOUNCE_STABLE_CHECKS=2    # 連續幾次穩定才觸發處理
SCAN_INTERVAL=300           # 定時全量掃描間隔（秒）
```

### Web 服務

```env
APP_HOST=0.0.0.0
APP_PORT=12010
APP_MODE=dev        # dev / prod
APP_DEBUG=false
APP_CORS_ORIGINS=http://localhost:5173
```

---

## 部署

### SMB 掛載

SMB 掛載由獨立腳本 `scripts/mount-smb.sh` 負責（需 root 權限），`deploy.sh` 會自動以 `sudo` 呼叫它。也可手動執行：

```bash
sudo ./scripts/mount-smb.sh
```

掛載流程：

1. 確認 `cifs-utils` 已安裝，否則中止
2. 讀取 `.env` 中的 `RECIPE_TRACE_SMB_*` 變數
3. 建立 `/mnt/eap_recipe`（如不存在）
4. 掛載前先檢查是否已掛載（idempotent，重複執行安全）
5. 使用臨時 credentials file 執行 `mount.cifs`，完成或失敗後立即刪除

掛載指令等同於：

```bash
sudo mount.cifs //<SMB_SERVER_IP>/<SHARE_NAME> /mnt/eap_recipe \
  -o credentials=/tmp/.smb_creds,vers=3.0,uid=$(id -u),gid=$(id -g),file_mode=0444,dir_mode=0555
```

### 執行部署

```bash
./scripts/deploy.sh
```

- **以一般使用者執行**（不需 `sudo ./scripts/deploy.sh`）
- 腳本以 `sudo` 呼叫 `mount-smb.sh` 處理掛載，其餘步驟以目前使用者身份執行
- 首次執行時 `sudo` 會提示輸入密碼
- 偏好使用 conda 環境（自動偵測 `CONDA_PREFIX`），無 conda 時 fallback 至 `.venv`

### 可用旗標

```bash
CONDA_ENV_NAME=myenv ./scripts/deploy.sh   # 指定 conda 環境名稱
RUN_NPM_CI=1 ./scripts/deploy.sh           # 強制重新安裝前端套件
```

---

## 啟動與管理

使用 `scripts/start.sh` 管理服務：

```bash
./scripts/start.sh start     # 背景啟動（pipeline + web）
./scripts/start.sh stop      # 停止服務
./scripts/start.sh restart   # 重啟
./scripts/start.sh status    # 查看狀態
```

日誌輸出至 `logs/ksbody-all.log`。

---

## CLI 指令

```bash
ksbody pipeline                        # 啟動 watcher pipeline
ksbody pipeline --process-file <path>  # 手動處理單一 recipe 檔案（驗證用）
ksbody web                             # 只啟動 Web API
ksbody all                             # pipeline + web 同時啟動
ksbody init-db                         # 建立資料庫 schema
```

---

## 異常排除

### `No valid watch paths available`

Pipeline 啟動時找不到任何有效的監控路徑。

**可能原因與對策：**

| 原因 | 解決方式 |
|------|----------|
| `.env` 缺少 `WATCH_PATHS` | 加入 `WATCH_PATHS=/mnt/eap_recipe/WBK_ConnX Elite` |
| `WATCH_PATHS` 使用 UNC 路徑（`\\server\share`） | 改為本地掛載路徑 `/mnt/...` |
| SMB 尚未掛載 | 執行 `sudo ./scripts/mount-smb.sh` 或 `./scripts/deploy.sh` |
| 掛載路徑不存在 | `ls /mnt/eap_recipe/` 確認；若不存在則重新執行 `sudo ./scripts/mount-smb.sh` |

確認掛載狀態：

```bash
mountpoint -q /mnt/eap_recipe && echo "mounted" || echo "not mounted"
ls "/mnt/eap_recipe/WBK_ConnX Elite/"
```

---

### SMB 掛載失敗

```
mount error(13): Permission denied
```

確認 `.env` 中的帳密正確，且帳號有讀取該 share 的權限：

```bash
smbclient //<SMB_SERVER_IP>/<SHARE_NAME> -U <SMB_USERNAME> -c "ls"
```

---

### `cifs-utils` 未安裝

```
ERROR: cifs-utils is not installed.
```

```bash
sudo apt install cifs-utils
```

---

### deploy.sh 執行後無任何輸出

**不要以 `sudo ./scripts/deploy.sh` 執行整個腳本**。應以一般使用者執行：

```bash
./scripts/deploy.sh   # 正確 — 內部只有 mount-smb.sh 以 sudo 執行
sudo ./scripts/deploy.sh   # 錯誤：sudo 會 strip conda PATH，導致 python 找不到
```

---

### conda 環境下 python 找不到

若 `activate_env` 偵測到 `CONDA_PREFIX` 但 `python` 仍找不到，確認 conda 環境已啟動：

```bash
conda activate ksbody
./scripts/deploy.sh
```

---

### 前端資源 404

前端需先打包才能由後端服務：

```bash
cd ksbody/web/frontend
npm install
npm run build
```

或執行 `RUN_NPM_CI=1 ./scripts/deploy.sh` 重新完整部署。

---

### 資料庫連線失敗

確認 `.env` 中的 `MYSQL_*` 設定正確，且資料庫已初始化：

```bash
ksbody init-db
```
