## Why

已完成 SMB 連線測試腳本（`scripts/test_smb_connection.py`）和 ENV 配置（`recipe-upload-connection` change），但 recipe 追溯 SMB 共享（`eap_recipe_tracebility`）尚未接入 watcher pipeline。需要先驗證測試腳本確認連線正常，再將此 SMB 路徑正式納入監控。

## What Changes

- 執行 `scripts/test_smb_connection.py` 驗證 SMB 連線可用性
- 將 recipe 追溯 SMB 共享路徑（`\\10.1.1.43\eap_recipe_tracebility\WBK_ConnX Elite`）加入 `config.yaml` 的 `watch_paths`
- 確保 watcher pipeline 能正確監控並處理來自此路徑的檔案

## Capabilities

### New Capabilities

_None — 利用現有 watcher 基礎設施，僅需配置新路徑。_

### Modified Capabilities

- `folder-watcher`: watch_paths 新增 recipe 追溯 SMB 共享路徑，watcher 需能同時監控多個 SMB 路徑

## Impact

- `config.yaml`: 新增 watch_paths 條目
- `watcher/observer.py`: 需確認 PollingObserver 支援多路徑監控
- `watcher/scanner.py`: FullScanner 需掃描新路徑
- 網路依賴：需要 SMB 連線到 `10.1.1.43` 的 `eap_recipe_tracebility` 共享
