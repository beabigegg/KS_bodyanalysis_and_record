## Why

專案需要將 RECIPE 上傳至追溯用網路空間 (`//10.1.1.43/eap_recipe_tracebility`)，以便後續追溯查詢。目前已取得連線帳密與路徑結構資訊，需將連線設定寫入 ENV 並驗證可連線、可存取目標目錄。

## What Changes

- 在 `web/.env` 和 `web/.env.example` 新增 SMB 連線變數（host、share、user、password）
- 新增連線測試腳本，驗證能否掛載/存取 `//10.1.1.43/eap_recipe_tracebility` 及其子目錄
- 記錄 recipe 檔案命名規則與目錄結構供後續上傳模組使用：
  - 路徑：`/WBK_ConnX Elite/<eqpid>/<recipe_file>`
  - 檔名格式：`L_WBK_ConnX Elite@<TYPE>@<BOP>@<WAFER>_<slot?>_<timestamp>`

## Capabilities

### New Capabilities
- `recipe-upload-connection`: SMB 連線設定與連線測試，包含 ENV 變數定義及連通性驗證腳本

### Modified Capabilities
（無）

## Impact

- **ENV 檔案**：`web/.env`、`web/.env.example` 新增 SMB 相關欄位
- **網路依賴**：需能存取 `10.1.1.43` 的 SMB 共享
- **安全性**：密碼存放於 `.env`（已在 `.gitignore` 中）
