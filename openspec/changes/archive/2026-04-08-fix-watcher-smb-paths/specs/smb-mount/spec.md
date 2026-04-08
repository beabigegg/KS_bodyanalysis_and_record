## ADDED Requirements

### Requirement: SMB share mounted during deployment
部署腳本 SHALL 在安裝依賴之前，自動將 recipe traceability SMB 共享掛載到本地目錄。

#### Scenario: First deployment with no existing mount
- **WHEN** 執行 `deploy.sh` 且 `/mnt/eap_recipe` 尚未掛載
- **THEN** 系統 SHALL 建立掛載目錄、使用 `.env` 中的 `RECIPE_TRACE_SMB_*` 認證變數執行 `mount.cifs`，掛載完成後刪除臨時 credentials file

#### Scenario: Redeployment with existing mount
- **WHEN** 執行 `deploy.sh` 且 `/mnt/eap_recipe` 已掛載
- **THEN** 系統 SHALL 跳過掛載步驟，輸出提示訊息後繼續部署

#### Scenario: cifs-utils not installed
- **WHEN** 執行 `deploy.sh` 且系統未安裝 `cifs-utils`
- **THEN** 系統 SHALL 輸出錯誤訊息並中止部署

### Requirement: SMB credentials sourced from .env
掛載腳本 SHALL 從 `.env` 既有的 `RECIPE_TRACE_SMB_*` 變數讀取認證資訊，不新增額外環境變數。

#### Scenario: Build mount command from env vars
- **WHEN** 掛載腳本執行
- **THEN** 系統 SHALL 使用 `RECIPE_TRACE_SMB_HOST` 和 `RECIPE_TRACE_SMB_SHARE` 組合 SMB 路徑，使用 `RECIPE_TRACE_SMB_USER` 和 `RECIPE_TRACE_SMB_PASSWORD` 建立臨時 credentials file

#### Scenario: Credentials file cleanup
- **WHEN** `mount.cifs` 執行完畢（無論成功或失敗）
- **THEN** 系統 SHALL 刪除臨時 credentials file
