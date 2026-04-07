## Context

目前 watcher pipeline 監控 `\\10.1.1.43\eap\prod\Recipe_Prod` 路徑的 recipe body 檔案。先前的 `recipe-upload-connection` change 已完成：
- SMB 連線測試腳本 `scripts/test_smb_connection.py`
- ENV 配置（`RECIPE_TRACE_SMB_*` 變數於 `web/.env`）

現在需要驗證 SMB 連線後，將 recipe 追溯共享路徑正式加入 watcher 監控。

## Goals / Non-Goals

**Goals:**
- 執行 SMB 連線測試，確認 `eap_recipe_tracebility` 共享可正常存取
- 將 `\\10.1.1.43\eap_recipe_tracebility\WBK_ConnX Elite` 加入 `config.yaml` 的 `watch_paths`
- 確保現有 watcher 架構（PollingObserver + FullScanner）能同時監控新舊路徑

**Non-Goals:**
- 不修改 parser 邏輯或資料庫 schema
- 不新增 watcher 程式碼（現有架構已支援多路徑）
- 不處理 SMB 自動重連機制（現有 `observer.py` 已有路徑不可用的日誌處理）

## Decisions

### Decision 1: 純配置變更，無程式碼修改

現有 `folder-watcher` spec 已定義支援多個 `watch_paths`。`observer.py` 的 `create_polling_observer` 會迭代所有路徑並分別 schedule。`FullScanner` 也接受多路徑清單。因此只需在 `config.yaml` 新增路徑即可。

**替代方案**: 為 recipe 追溯建立獨立 watcher 服務 → 不必要，現有架構已支援。

### Decision 2: 先測試再接入

在修改 `config.yaml` 前，先執行 `test_smb_connection.py` 驗證連線。這確保配置的路徑實際可達，避免 watcher 啟動後因路徑不可用而產生大量錯誤日誌。

## Risks / Trade-offs

- **[SMB 連線不穩定]** → 現有 watcher 已有錯誤日誌機制，路徑不可用時不會中斷其他路徑監控
- **[檔案格式不同]** → recipe 追溯路徑下的檔案若不符合 `RECIPE_BODY_PATTERN`，handler 會自動忽略，不影響 pipeline
- **[效能影響]** → 新增一個 watch path 會增加 PollingObserver 的掃描負擔，但 recipe 追溯路徑檔案量不大，影響可忽略
