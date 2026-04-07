## 0. 環境前置

- [x] 0.1 所有測試與執行步驟 SHALL 使用專案的 conda 環境 `ksbody`（`conda activate ksbody`）

## 1. 驗證 SMB 連線

- [x] 1.1 在 `ksbody` 環境下執行 `python scripts/test_smb_connection.py`，確認連線成功並記錄輸出的 eqpid 子目錄清單
- [x] 1.2 確認目標路徑 `\\10.1.1.43\eap_recipe_tracebility\WBK_ConnX Elite` 下存在預期的檔案結構

## 2. 更新 watch_paths

- [x] 2.1 在 `config.yaml` 的 `watch_paths` 新增 `\\\\10.1.1.43\\eap_recipe_tracebility\\WBK_ConnX Elite`
- [x] 2.2 確認新路徑格式與現有路徑一致（UNC 路徑、雙反斜線跳脫）

## 3. 啟動與驗證

- [x] 3.1 啟動 watcher service（`python main.py`），確認兩個 watch_paths 皆成功被 PollingObserver 排程
- [x] 3.2 檢查日誌輸出，確認無路徑不可用的錯誤訊息

