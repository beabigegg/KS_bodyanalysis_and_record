## 1. ENV 設定

- [x] 1.1 在 `web/.env.example` 新增 `RECIPE_TRACE_SMB_*` 變數區塊與註解說明
- [x] 1.2 在 `web/.env` 填入實際連線資訊（host=10.1.1.43, share=eap_recipe_tracebility, user=tracerecipe, password, machine_folder=WBK_ConnX Elite）

## 2. 連線測試腳本

- [x] 2.1 建立 `scripts/test_smb_connection.py`，從 `web/.env` 讀取 `RECIPE_TRACE_SMB_*` 變數
- [x] 2.2 實作 `net use` 掛載邏輯，使用 `/user:` 指定帳密連線至目標共享
- [x] 2.3 實作連通性驗證：列出 `WBK_ConnX Elite` 下的 eqpid 子目錄
- [x] 2.4 實作錯誤處理：區分網路不通、帳密錯誤、共享路徑不存在三種失敗情境
- [x] 2.5 連線測試完成後執行 `net use /delete` 清理掛載

## 3. 驗證

- [x] 3.1 執行測試腳本，確認可成功連線並列出目錄內容
