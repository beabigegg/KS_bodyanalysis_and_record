## 1. BNDRegistryParser 核心實作

- [x] 1.1 建立 `parsers/bnd_registry.py`，定義 `ParmsEntry`、`RefEntry`、`ComponentRegistry` dataclass
- [x] 1.2 實作 `BNDRegistryParser.parse(bnd_path, extracted_dir)` 方法，解析 BND top-level 宣告區的單一角色關鍵字（`mag_handler`、`workholder`、`lead_frame`、`magazine`、`heat_block`、`indexer_ref_system`）
- [x] 1.3 實作解析多個 `parms` 宣告：提取 stem 與 `has_bsg`（是否跟隨 `ball` 關鍵字）
- [x] 1.4 實作解析多個 `ref` 宣告：提取 stem 後，讀取對應 REF 檔前 20 行，取得 `ref_type`（DIE/LEAD）和 `name` 欄位
- [x] 1.5 實作解析 `master_device` block：取得 `master_wire_chain` 的 WIR stem
- [x] 1.6 實作 graceful fallback：缺少必要欄位時設為 `None` 並記錄 warning，不拋出例外

## 2. Pipeline：BND-first 解析流程

- [x] 2.1 在 `pipeline.py` 的解析迴圈中，第一步先呼叫 `BNDRegistryParser.parse()` 建立 `ComponentRegistry`
- [x] 2.2 實作 `resolve_role(stem, file_type, registry)` 函數，回傳語意角色字串（`"mag_handler"`、`"workholder"`、`"parms"`、`"die_ref"` 等）或 `None`
- [x] 2.3 修改 `pipeline.py` 解析迴圈：解析每個 component 檔案時，呼叫 `resolve_role` 取得 role，若 role 非 None 則 param_name 加上 `<role>/` 前綴
- [x] 2.4 移除舊的 `DIE_SPECIFIC_FILE_TYPES` 前綴邏輯（由新的 `resolve_role` 取代）
- [x] 2.5 確認 `LF`、`MAG`、`HB`、`IRS` 的 role 回傳 `None`（不加前綴）

## 3. BSG-aware parms_2 合併邏輯

- [x] 3.1 在 `pipeline.py` 中，當 `parms_list` 有 2 個以上項目時，呼叫 `should_keep_parms_2(p1, p2, parsed_params)` 判斷
- [x] 3.2 實作 `should_keep_parms_2`：`has_bsg` 不同 → True；`has_bsg` 相同且 param_values 不同 → True；否則 → False
- [x] 3.3 當 `should_keep_parms_2 = False` 時，只保留第一組 PRM（`parms/`），丟棄第二組
- [x] 3.4 當 `should_keep_parms_2 = True` 時，兩組都保留（`parms/` 和 `parms_2/`）

## 4. 單元測試

- [x] 4.1 撰寫 `BNDRegistryParser` 單元測試：驗證從 PJA3406 BND 解析出 `mag_handler="CJ621A20"`、`workholder="CJ621A41"`、`wire_stem="CJ621A20"`
- [x] 4.2 撰寫 `BNDRegistryParser` 單元測試：驗證從 PJA3406 BND 解析出 `parms_list` 有 2 個項目，第一個 `has_bsg=True`，第二個 `has_bsg=False`
- [x] 4.3 撰寫 `BNDRegistryParser` 單元測試：驗證從 REF 檔讀取 `ref_type`，`AP643419.REF` 回傳 `ref_type="DIE"`
- [x] 4.4 撰寫 `resolve_role` 單元測試：`("CJ621A20", "PHY")` → `"mag_handler"`；`("CJ621A41", "PHY")` → `"workholder"`
- [x] 4.5 撰寫 `resolve_role` 單元測試：`("CJ621A20", "LF")` → `None`；`("CJ621A20", "PRM")` → `"parms"`
- [x] 4.6 撰寫 `should_keep_parms_2` 單元測試：`has_bsg=(True, False)` → `True`；值完全相同且 BSG 相同 → `False`
- [x] 4.7 撰寫 pipeline 整合測試：驗證 PJA3406 import 後 `mag_handler/IN_FIRST_SLOT` 存在於 recipe_params
- [x] 4.8 撰寫 pipeline 整合測試：驗證 PJA3406 import 後 `die_ref/num_sites` 和 `lead_ref/num_sites` 各自存在

## 5. 資料遷移

- [x] 5.1 清空測試 DB 的所有 recipe 相關資料表（同 fix-compare-and-extraction-gaps 的 7.1 步驟）
- [x] 5.2 重新 import PJA3406 和 PJS6400，確認 param_name 格式為語意前綴（`mag_handler/`、`workholder/`、`parms/`、`die_ref/`、`lead_ref/`）
- [x] 5.3 確認 LF/MAG/HB 參數無前綴（直接 param_name，file_type 標識）
- [x] 5.4 確認 PJA3406 的 `parms_2/` 存在（因 BSG 差異），PJS6400 只有 `parms/`
