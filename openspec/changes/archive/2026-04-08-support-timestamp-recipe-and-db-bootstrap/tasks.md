## 1. Filename Rule Updates

- [x] 1.1 收斂 recipe body 檔名 regex / helper，支援 `..._<recipe_version>` 與 `..._<recipe_version>_<timestamp>`
- [x] 1.2 更新 watcher event handler、full scanner、watcher status/files API 使其共用新檔名判定
- [x] 1.3 更新 metadata extractor，使其可忽略 timestamp 尾碼並維持既有 `recipe_version` 解析
- [x] 1.4 補上舊格式與 timestamp 尾碼格式的 watcher / parser 測試

## 2. Database Bootstrap

- [x] 2.1 在 `ksbody.db` 提供可重用的 shared schema bootstrap function，建立所有 `ksbody_*` 資料表與索引
- [x] 2.2 讓 `python -m ksbody pipeline` 與 `python -m ksbody web` 在服務啟動前自動執行 bootstrap
- [x] 2.3 讓 `python -m ksbody all` 由主程序先完成 bootstrap，再啟動 pipeline / web 子程序
- [x] 2.4 補上空資料庫、既有資料庫與重複執行 bootstrap 的測試或驗證

## 3. Documentation And Validation

- [x] 3.1 更新 README，說明 timestamp 尾碼檔名格式與 schema bootstrap 行為
- [x] 3.2 以實際 SMB 路徑或等價測試資料驗證 timestamp 尾碼檔案能被 watcher 偵測
- [x] 3.3 驗證在缺少資料表的 MySQL 上啟動服務時，`ksbody_*` schema 會自動建立且不影響既有資料
