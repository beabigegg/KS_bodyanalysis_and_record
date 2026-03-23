## 1. 專案結構與配置

- [x] 1.1 建立專案目錄結構（parsers/、db/、watcher/、config/）和 requirements.txt（watchdog, sqlalchemy, pymysql, pyyaml）
- [x] 1.2 建立 config.yaml 配置檔，包含 watch_paths、mysql 連線、debounce 設定、scan_interval
- [x] 1.3 建立配置載入模組 config/settings.py，讀取並驗證 YAML 配置

## 2. 資料庫

- [x] 2.1 建立 MySQL 資料表定義模組 db/schema.py，使用 SQLAlchemy Core 定義 recipe_import、recipe_params、recipe_app_spec、recipe_bsg、recipe_rpm_limits、recipe_rpm_reference 六張表
- [x] 2.2 建立資料表建立腳本 db/init_db.py，執行 CREATE TABLE（含索引）
- [x] 2.3 建立資料寫入模組 db/repository.py，實作 transaction 包裝的批量 insert 方法

## 3. Recipe 解壓與 Metadata 提取

- [x] 3.1 建立 extractor/metadata.py，實作從檔案路徑提取 machine_type、machine_id，從檔名提取 product_type、bop、wafer_pn、recipe_version
- [x] 3.2 建立 extractor/decompress.py，實作 gzip tar 解壓到暫存目錄，含 context manager 自動清理

## 4. Recipe 解析器

- [x] 4.1 建立 parsers/base.py，定義 BaseParser 抽象類別（parse 方法回傳統一的 dict 結構）
- [x] 4.2 建立 parsers/key_value_parser.py，解析 PHY、PRM、LF、MAG 的 `symbol = value units ... min max default` 格式
- [x] 4.3 建立 parsers/sectioned_parser.py，解析 BND、REF、HB、WIR、BSG、AIC 的 section/block 格式（含巢狀 `{ }` 處理）
- [x] 4.4 建立 parsers/app_parser.py，解析 APP 的 `key=value` 格式，產出 recipe_app_spec 寬表資料
- [x] 4.5 建立 parsers/csv_parser.py，解析 AID 的 CSV 格式量測項目定義
- [x] 4.6 建立 parsers/sqlite_parser.py，讀取 RPM SQLite，提取 rpm_limits 和 rpm_reference_data
- [x] 4.7 建立 parsers/monitor_parser.py，解析 LHM、VHM 的 `key = value` 加 `loop_id N { }` 巢狀格式
- [x] 4.8 建立 parsers/registry.py，根據副檔名映射到對應的 parser class

## 5. 解析流程整合

- [x] 5.1 建立 pipeline.py，串接完整流程：接收檔案路徑 → 提取 metadata → 解壓 → 遍歷所有檔案呼叫對應 parser → 寫入 MySQL → 清理暫存
- [x] 5.2 加入錯誤處理：單一檔案解析失敗不中斷整體流程，記錄日誌後繼續

## 6. 資料夾監聽服務

- [x] 6.1 建立 watcher/observer.py，使用 watchdog PollingObserver 遞迴監聽配置路徑
- [x] 6.2 建立 watcher/handler.py，實作 FileSystemEventHandler，含 debounce 邏輯（等待 mtime 穩定）和檔名格式過濾
- [x] 6.3 建立 watcher/scanner.py，實作定期全量掃描補償機制，比對檔案 mtime 與最後入庫時間

## 7. 主程式與日誌

- [x] 7.1 建立 main.py 入口，初始化配置、資料庫、啟動 watcher 服務
- [x] 7.2 配置 logging（console + file），含 recipe 解析成功/失敗的結構化日誌

## 8. 測試與驗證

- [x] 8.1 使用現有的 `L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1` 測試完整解析流程
- [x] 8.2 驗證 MySQL 資料正確性：檢查 recipe_import 記錄、recipe_params 參數數量、recipe_app_spec 耗材資訊、RPM 資料
- [x] 8.3 測試重複解析同一檔案，確認產生新記錄而非覆蓋
