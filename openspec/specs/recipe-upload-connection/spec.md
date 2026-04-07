# recipe-upload-connection Specification

## Purpose
TBD - created by archiving change recipe-upload-connection. Update Purpose after archive.
## Requirements
### Requirement: ENV 定義 recipe 追溯 SMB 連線變數
系統 SHALL 在 `web/.env` 及 `web/.env.example` 中定義以下環境變數：
- `RECIPE_TRACE_SMB_HOST`：SMB 伺服器 IP
- `RECIPE_TRACE_SMB_SHARE`：共享名稱
- `RECIPE_TRACE_SMB_USER`：連線帳號
- `RECIPE_TRACE_SMB_PASSWORD`：連線密碼
- `RECIPE_TRACE_SMB_MACHINE_FOLDER`：機台型號資料夾名稱

#### Scenario: ENV 檔案包含所有必要變數
- **WHEN** 開發者查看 `web/.env.example`
- **THEN** 檔案 SHALL 包含所有 `RECIPE_TRACE_SMB_*` 變數及說明註解

#### Scenario: ENV 實際值已填入
- **WHEN** 開發者查看 `web/.env`
- **THEN** 所有 `RECIPE_TRACE_SMB_*` 變數 SHALL 填入正確的連線資訊

### Requirement: SMB 連線測試腳本
系統 SHALL 提供獨立的連線測試腳本 `scripts/test_smb_connection.py`，可驗證 recipe 追溯 SMB 共享的連通性。

#### Scenario: 連線成功
- **WHEN** 執行 `python scripts/test_smb_connection.py` 且網路連通、帳密正確
- **THEN** 腳本 SHALL 顯示連線成功訊息，並列出目標共享下 `WBK_ConnX Elite` 資料夾中的 eqpid 子目錄清單

#### Scenario: 連線失敗 — 網路不通
- **WHEN** 執行測試腳本且 SMB 伺服器無法連線
- **THEN** 腳本 SHALL 顯示明確錯誤訊息，指出網路連線問題

#### Scenario: 連線失敗 — 帳密錯誤
- **WHEN** 執行測試腳本且帳號或密碼不正確
- **THEN** 腳本 SHALL 顯示明確錯誤訊息，指出認證失敗

#### Scenario: 連線失敗 — 共享路徑不存在
- **WHEN** 執行測試腳本且共享名稱不正確
- **THEN** 腳本 SHALL 顯示明確錯誤訊息，指出共享路徑無法存取

