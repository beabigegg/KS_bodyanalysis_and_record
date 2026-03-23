## Why

KS ConnX Elite 打線機的 recipe body 資料目前以 gzip tar 壓縮檔形式存放在網路共享路徑，無法直接查閱或比對參數。生產端需要：(1) 跨機台比較同產品的 recipe 參數差異、(2) 追蹤同機台不同時間點的參數變化並關聯 LOT ID 與最終測試良率、(3) 未來引入 Run-to-Run 控制進行參數 fine-tune。現有的 `ks_body_to_recipe.py` 僅完成解壓還原，缺乏解析、結構化儲存和自動化監聽能力。

## What Changes

- 建立資料夾監聽服務，自動偵測 `\\10.1.1.43\eap\prod\Recipe_Prod\` 下新增或修改的 recipe body 檔案
- 從路徑結構自動提取 machine_type、machine_id；從檔名解析 product_type、bop、wafer_pn
- 解壓 gzip tar 並解析所有內含檔案（BND、PRM、PHY、LF、MAG、APP、BSG、WIR、REF、LHM、VHM、AIC、AID、PPC、HB），全參數入庫
- 特殊處理 RPM 檔案（SQLite 格式），提取 limits 和 reference data
- 將結構化資料寫入 MySQL，主表 + EAV 參數表 + 專用寬表（耗材、Ball Signature、RPM）
- 提供 lot_id 欄位預留接口，供後續 MES/EAP 對接

## Capabilities

### New Capabilities
- `folder-watcher`: 監聽網路共享資料夾，偵測 recipe body 檔案新增/修改事件，觸發解析流程
- `recipe-extractor`: 解壓 gzip tar 格式的 recipe body，從路徑與檔名提取 metadata
- `recipe-parser`: 解析所有 recipe 檔案格式（key-value、tabular、sectioned、CSV、SQLite），產出結構化資料
- `database-storage`: MySQL 資料模型設計與寫入，包含 recipe_import 主表、recipe_params (EAV)、recipe_app_spec、recipe_bsg、recipe_rpm_limits、recipe_rpm_reference

### Modified Capabilities

(無既有 spec)

## Impact

- **新增依賴**: watchdog (資料夾監聽)、pymysql/SQLAlchemy (MySQL)、sqlite3 (RPM 解析)
- **網路存取**: 需要掛載或存取 `\\10.1.1.43` 共享路徑
- **MySQL**: 使用 mysql.theaken.com:33306 db_A060，新增 6 張資料表
- **現有程式**: `ks_body_to_recipe.py` 的解壓邏輯將被整合進 recipe-extractor 模組
