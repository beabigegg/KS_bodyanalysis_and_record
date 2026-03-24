## Why

目前的 Recipe 提取與跨機台比較功能存在多項系統性缺口：RPM 資料完全未被比較、`None` 值邏輯錯誤導致「一台有另一台沒有」的參數被靜默略過、BSG 資料重複出現在兩個比較區塊、以及多 die 檔案共用同一 `param_name` 導致 die 身份資訊喪失。這些問題使得比較結果不完整且在部分情境下不可信賴。

## What Changes

- **新增 RPM 比較區塊**：`compare.py` 加入 `recipe_rpm_limits` 和 `recipe_rpm_reference` 的跨機台比對邏輯，前端 `ComparePage` 新增 RPM Diff 區塊
- **修正 None 差異判斷**：`_diff_rows` 函數將「一方有值、另一方為 None」視為差異（`is_diff = True`），而非目前的靜默略過
- **消除 BSG 重複**：compare 的 `params` 查詢排除 `file_type = 'BSG'`，BSG 資料僅保留在結構化的 `bsg` 區塊
- **多 die 參數加前綴**：import pipeline 在儲存 PHY/PRM/LF/MAG/REF 等 die 專屬檔案時，將 die 代碼（檔名前綴）加入 `param_name`，格式為 `<die_code>/<param_name>`
- **移除 AID 無效 params**：AID 檔案為量測定義清單，無數值可比較，import 時不寫入 `recipe_params`（或標記為 non-comparable）
- **更新相關 Spec**：`cross-machine-compare` 和 `recipe-parser` 的需求規格補上上述缺口

## Capabilities

### New Capabilities
- `rpm-comparison`: 跨機台 RPM limits 與 RPM reference 統計值的比較功能

### Modified Capabilities
- `cross-machine-compare`: 新增 RPM 比較區塊、修正 None 判斷邏輯、排除 BSG 在 params 中的重複
- `recipe-parser`: 定義多 die 檔案的 param_name 命名規則（die 前綴）、明確 AID 資料不存入 recipe_params

## Impact

**後端**
- `web/routes/compare.py`：加入 RPM 查詢與 diff 邏輯、修改 `_diff_rows` 的 None 判斷、params 查詢排除 BSG
- `pipeline.py`：parse 多 die 檔案時為 param_name 加上 die 代碼前綴
- `parsers/csv_parser.py`：AID 解析不產生 params（或 pipeline 層過濾）
- `db/schema.py`：`param_name` 欄位長度需可容納 `<die_code>/<param_name>` 格式（目前 VARCHAR 1024，應足夠）

**前端**
- `web/frontend/src/pages/ComparePage.tsx`：新增 RPM Diff 區塊（limits + reference 分開）
- `web/frontend/src/types.ts`：擴充 `ComparePayload` 型別

**資料庫**
- 現有資料（舊格式 param_name）需要 migration 或重新 import，因為加入 die 前綴屬 **BREAKING** 變更
- **BREAKING**：`param_name` 格式從 `Bond1_Force_Seg_01` 改為 `CJ621A20/Bond1_Force_Seg_01`，現有資料需重新 import
