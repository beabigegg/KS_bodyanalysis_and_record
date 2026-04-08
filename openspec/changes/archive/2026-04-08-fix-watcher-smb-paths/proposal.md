## Why

Pipeline 啟動後因 `WATCH_PATHS` 未設定而反覆 crash（`RuntimeError: No valid watch paths available`），重試 5 次後被 ProcessManager 停用。根本原因有二：
1. `.env` 遺漏 `WATCH_PATHS` 變數
2. `.env.example` 使用 Windows UNC 路徑（`\\10.1.1.43\...`），Linux 環境無法直接存取，需先掛載 SMB 到本地目錄

## What Changes

- 在 `deploy.sh` 中加入 SMB 掛載步驟，將 `//10.1.1.43/eap_recipe_tracebility` 掛載到本地路徑（如 `/mnt/eap_recipe`），部署時自動確保掛載就緒
- 修正 `.env` 加入 `WATCH_PATHS=/mnt/eap_recipe/WBK_ConnX Elite`，指向掛載後的目錄（遞迴監控所有機台子資料夾）
- 更新 `.env.example` 範例路徑為 Linux mount path 格式
- 確認 observer `recursive=True` 已覆蓋所有 `{machine_id}/L_*` 檔案，無需在 env 中逐一指定機台

## Capabilities

### New Capabilities
- `smb-mount`: SMB 共享掛載設定與腳本，確保 Linux 環境可存取 recipe traceability 網路資料夾

### Modified Capabilities
- `folder-watcher`: watch path 由 UNC 路徑改為本地掛載路徑，確認遞迴監控機台層級的行為
- `unified-config`: `.env.example` 中 `WATCH_PATHS` 範例更新為 Linux 本地掛載路徑格式

## Impact

- **配置**: `.env` 和 `.env.example` 的 `WATCH_PATHS` 值變更
- **部署**: `deploy.sh` 新增 SMB mount 步驟，部署即掛載，確保 pipeline 啟動前路徑可用
- **執行環境**: 需要 `cifs-utils` 套件支援 SMB 掛載
- **現有程式碼**: observer / scanner / handler 邏輯不需修改，僅路徑配置變更
