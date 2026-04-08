## 1. SMB 掛載

- [x] 1.1 在 `deploy.sh` 加入 `cifs-utils` 檢查，未安裝則中止部署
- [x] 1.2 在 `deploy.sh` 加入 SMB 掛載函式：從 `.env` 讀取 `RECIPE_TRACE_SMB_*` 變數，建立臨時 credentials file，執行 `mount.cifs`，掛載完成後刪除 credentials file
- [x] 1.3 掛載邏輯設為 idempotent：`mountpoint -q` 檢查已掛載則跳過

## 2. 配置修正

- [x] 2.1 `.env` 加入 `WATCH_PATHS=/mnt/eap_recipe/WBK_ConnX Elite`
- [x] 2.2 `.env.example` 的 `WATCH_PATHS` 範例從 UNC 路徑改為 `/mnt/eap_recipe/WBK_ConnX Elite`

## 3. 驗證

- [x] 3.1 執行 `deploy.sh` 確認 SMB 掛載成功，`/mnt/eap_recipe/WBK_ConnX Elite` 可存取
- [x] 3.2 啟動 pipeline 確認 watcher 正常啟動，不再出現 `No valid watch paths available` 錯誤
- [x] 3.3 確認 observer 遞迴偵測到機台子資料夾（GWBK_TEST1、GWBK_TEST2）中的 recipe body 檔案
