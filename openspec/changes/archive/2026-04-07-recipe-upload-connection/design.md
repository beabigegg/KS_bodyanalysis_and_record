## Context

專案目前透過 `config.yaml` 中的 `watch_paths` 以 UNC 路徑直接存取 `\\10.1.1.43\eap\prod\Recipe_Prod` 來監控 recipe 檔案。現在需要新增一條連線至 `\\10.1.1.43\eap_recipe_tracebility`，用於上傳 recipe 追溯資料。此路徑需要帳號密碼驗證（不同於現有 watch_paths 可能使用的系統快取憑證）。

目錄結構：
```
\\10.1.1.43\eap_recipe_tracebility\
  └── WBK_ConnX Elite\
      └── <eqpid>\
          └── L_WBK_ConnX Elite@<TYPE>@<BOP>@<WAFER>_<seq>_<timestamp>
```

## Goals / Non-Goals

**Goals:**
- 將 recipe 追溯上傳的 SMB 連線資訊集中管理於 ENV 檔案
- 提供連線測試腳本，驗證能否以指定帳密存取目標共享及子目錄
- 確認可列出 `WBK_ConnX Elite` 下的 eqpid 資料夾與 recipe 檔案

**Non-Goals:**
- 不實作 recipe 上傳邏輯（後續 change 處理）
- 不修改現有 `watch_paths` 或 `config.yaml` 的讀取機制
- 不處理 recipe 檔名解析（已有 recipe-parser spec）

## Decisions

### 1. 連線方式：Windows UNC + `net use` 掛載

在 Windows 環境下，使用 `subprocess` 呼叫 `net use` 掛載網路磁碟，而非引入第三方 SMB 套件（如 smbprotocol）。

**理由**：
- 專案執行環境為 Windows，`net use` 是原生支援
- 現有 `watch_paths` 已使用 UNC 路徑，保持一致性
- 避免新增外部依賴

**替代方案**：
- `smbprotocol` Python 套件：跨平台但增加依賴，目前不需要

### 2. 憑證管理：ENV 變數

連線帳密存放於 `web/.env`，透過環境變數讀取，不寫入 `config.yaml`。

**理由**：
- `.env` 已在 `.gitignore` 中，安全性較高
- 與現有 MySQL/Oracle 憑證管理方式一致
- `config.yaml` 已提交版控，不適合存放密碼

### 3. ENV 變數命名

```
RECIPE_TRACE_SMB_HOST=10.1.1.43
RECIPE_TRACE_SMB_SHARE=eap_recipe_tracebility
RECIPE_TRACE_SMB_USER=tracerecipe
RECIPE_TRACE_SMB_PASSWORD=<secret>
RECIPE_TRACE_SMB_MACHINE_FOLDER=WBK_ConnX Elite
```

### 4. 測試腳本位置

放置於 `scripts/test_smb_connection.py`，可獨立執行，不依賴 web 服務。

## Risks / Trade-offs

- **`net use` 憑證衝突** → 使用 `/user:` 參數明確指定帳號，避免與系統快取衝突。測試後用 `net use /delete` 清理。
- **網路不通** → 測試腳本需有明確的錯誤訊息，區分網路不通 vs 帳密錯誤 vs 權限不足。
- **共享路徑含空格**（`WBK_ConnX Elite`）→ 路徑需以引號包裹處理。
