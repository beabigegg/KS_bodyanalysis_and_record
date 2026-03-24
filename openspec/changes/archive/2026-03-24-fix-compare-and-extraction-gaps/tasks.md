## 1. Pipeline：修正 die 專屬參數前綴

- [x] 1.1 在 `pipeline.py` 定義 die 專屬 file_type 集合（`DIE_SPECIFIC_FILE_TYPES = {"PHY", "PRM", "LF", "MAG", "REF"}`）
- [x] 1.2 在 pipeline 的 parse 迴圈中，當 `file_type in DIE_SPECIFIC_FILE_TYPES` 時，從 `candidate.stem` 提取 die_code，並對 params 中的每個 `param_name` 加上 `<die_code>/` 前綴
- [x] 1.3 確認 `param_name` 的 dedup key 改為 `(file_type, param_name_with_prefix)`，不再有兩個 die 覆蓋彼此的問題
- [x] 1.4 撰寫單元測試：驗證 `CJ621A20.PRM` 產出的 param_name 格式為 `CJ621A20/Bond1_Force_Seg_01`
- [x] 1.5 撰寫單元測試：驗證 `MR192600.BND` 產出的 param_name 無前綴

## 2. Pipeline：移除 AID 寫入 recipe_params

- [x] 2.1 在 `pipeline.py` 中，在 `params.extend(parsed.params)` 之前，過濾掉 `file_type == "AID"` 的項目
- [x] 2.2 撰寫單元測試：驗證 import AID 檔案後 recipe_params 中無任何 `file_type = 'AID'` 記錄

## 3. Compare：修正 None 差異判斷邏輯

- [x] 3.1 修改 `compare.py` 的 `_diff_rows` 函數，將 None 判斷改為：有任一方有值且有任一方為 None 時，`is_diff = True`
- [x] 3.2 撰寫單元測試：`val_map = {1: "150", 2: None}` 時 `is_diff = True`
- [x] 3.3 撰寫單元測試：`val_map = {1: None, 2: None}` 時 `is_diff = False`（雙方都沒有不算差異）

## 4. Compare：排除 BSG 在 params 區段的重複

- [x] 4.1 修改 `compare.py` 中的 `param_stmt`，加入 `.where(recipe_params.c.file_type != "BSG")`
- [x] 4.2 驗證：比較結果中 `params` 區段不再出現 `file_type = 'BSG'` 的項目

## 5. Compare 後端：新增 RPM diff 邏輯

- [x] 5.1 在 `compare.py` 中 import `recipe_rpm_limits` 和 `recipe_rpm_reference`
- [x] 5.2 實作 `_diff_rpm_rows(keys, value_fields, source_rows, import_ids, show_all)` 函數，支援多值欄位輸出（每個 key 對應多個 field 的比較值）
- [x] 5.3 撰寫 RPM limits 查詢：key = `(signal_name, property_name, rpm_group, bond_type, measurement_name, limit_type, statistic_type, parameter_set)`，value_fields = `[lower_limit, upper_limit, active]`
- [x] 5.4 撰寫 RPM reference 查詢：key = `(signal_name, property_name, rpm_group, bond_type, measurement_name, source)`，value_fields = `[average, median, std_dev, median_abs_dev, minimum, maximum, sample_count]`
- [x] 5.5 將 `rpm_limits` 和 `rpm_reference` 加入 compare endpoint 的回傳結構（`data` 物件）
- [x] 5.6 更新 `CompareRequest` 或回傳型別的文件/註解，說明新欄位

## 6. Compare 前端：新增 RPM Diff 區塊

- [x] 6.1 更新 `web/frontend/src/types.ts`，在 `ComparePayload` 型別中新增 `rpm_limits` 和 `rpm_reference` 欄位（`CompareRow[]`）
- [x] 6.2 在 `ComparePage.tsx` 的結果區域中，於 BSG Diff 之後新增 `<h3>RPM Limits Diff</h3>` 和對應的 `<DiffTable>` 元件
- [x] 6.3 在 `ComparePage.tsx` 中，於 RPM Limits Diff 之後新增 `<h3>RPM Reference Diff</h3>` 和對應的 `<DiffTable>` 元件
- [x] 6.4 確認 `DiffTable` 元件能正確顯示 RPM 多欄位格式（若 DiffTable 只支援單一值欄位，需調整或新建元件）

## 7. 整合測試與資料遷移

- [x] 7.1 清空測試 DB 的 recipe 相關資料表（recipe_import + 所有 FK 關聯表）
- [x] 7.2 用新版 pipeline 重新 import 兩個 sample recipe body（PJA3406、PJS6400），確認 param_name 帶有 die 前綴
- [x] 7.3 執行跨機台比較（PJA3406 vs PJS6400），確認：
  - `params` 區段含有 `CJ621A20/Bond1_Force_Seg_01` 格式的項目
  - `params` 區段無任何 `file_type = 'BSG'` 項目
  - `bsg` 區段仍正常顯示
  - `rpm_limits` 區段有資料且差異正確標記
  - `rpm_reference` 區段有資料
- [x] 7.4 驗證 None 修正：手動插入一筆只有部分機台有值的 recipe_params 記錄，確認 compare 結果中 `is_diff = true`

