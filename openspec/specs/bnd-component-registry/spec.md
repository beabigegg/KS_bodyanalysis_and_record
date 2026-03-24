## ADDED Requirements

### Requirement: Parse BND to build ComponentRegistry
系統 SHALL 在處理 recipe 壓縮包時，先解析 BND 主檔，建立 `ComponentRegistry`，記錄每個 component 檔案的機台角色（role）。

**BND top-level 宣告關鍵字（一對一角色）**：
- `mag_handler` → 進出料 Magazine Handler 的 PHY 設定
- `workholder` → 夾持承載台的 PHY 設定
- `lead_frame` → 導線架尺寸設定
- `magazine` → 料盒設定
- `heat_block` → 加熱台設定
- `indexer_ref_system` → 索引參考系統

**BND top-level 宣告關鍵字（可多個）**：
- `parms <stem>.PRM [ball <stem>.BSG]` → 焊接參數組（可有多個）
- `ref <stem>.REF eyepoints <stem>.EYE` → 參考系統（可有多個）

**`master_device` block**：
- `master_wire_chain 0 <stem>.WIR` → 線路連接定義檔

#### Scenario: Extract single-role MHS assignments
- **WHEN** BND 包含 `mag_handler  CJ621A20.PHY` 和 `workholder  CJ621A41.PHY`
- **THEN** `ComponentRegistry.mag_handler = "CJ621A20"` 且 `ComponentRegistry.workholder = "CJ621A41"`

#### Scenario: Extract multiple parms entries
- **WHEN** BND 包含兩行 `parms`：`parms CJ621A20.PRM ball CJ621A20.BSG` 和 `parms CJ621A41.PRM`
- **THEN** `parms_list = [ParmsEntry(stem="CJ621A20", has_bsg=True), ParmsEntry(stem="CJ621A41", has_bsg=False)]`

#### Scenario: Extract wire stem from master_device block
- **WHEN** `master_device 1 { ... master_wire_chain 0 CJ621A20.WIR }` 出現在 BND 中
- **THEN** `ComponentRegistry.wire_stem = "CJ621A20"`

#### Scenario: BND with single parms entry
- **WHEN** BND 只有一行 `parms AP643419.PRM ball AP643419.BSG`
- **THEN** `parms_list = [ParmsEntry(stem="AP643419", has_bsg=True)]`

### Requirement: Read REF file ref_type to classify reference systems
系統 SHALL 在建立 ComponentRegistry 時，開啟每個被 BND 宣告的 REF 檔，讀取其內部的 `ref_type` 欄位（`DIE` 或 `LEAD`），作為 REF 的語意角色分類依據。

#### Scenario: Classify DIE reference system
- **WHEN** BND 宣告 `ref AP643419.REF eyepoints AP643419.EYE`，且 `AP643419.REF` 內部包含 `ref_type = DIE`
- **THEN** `ref_list` 中對應項目的 `ref_type = "DIE"`，pipeline 使用前綴 `die_ref`

#### Scenario: Classify LEAD reference system
- **WHEN** BND 宣告 `ref CJ621A20.REF eyepoints CJ621A20.EYE`，且 `CJ621A20.REF` 內部包含 `ref_type = LEAD`
- **THEN** `ref_list` 中對應項目的 `ref_type = "LEAD"`，pipeline 使用前綴 `lead_ref`

#### Scenario: REF file not accessible
- **WHEN** BND 宣告了一個 REF 但對應檔案無法讀取
- **THEN** 系統 SHALL 記錄 warning，該 REF 的 ref_type 設為 `"UNKNOWN"`，前綴使用 `ref_N`（N 為順序號）

### Requirement: Graceful fallback when BND parsing fails
系統 SHALL 在 BND 解析失敗時（格式異常、缺少關鍵字），以 fallback 策略繼續 import，不中斷整體流程。

#### Scenario: BND missing expected keywords
- **WHEN** BND 不包含 `mag_handler` 或 `workholder` 關鍵字
- **THEN** 系統 SHALL 記錄 warning，對應欄位設為 `None`，相關 component 檔案的 param_name 使用 `Path(file).stem` 作為前綴（舊行為 fallback）

#### Scenario: BND file not found in archive
- **WHEN** 解壓目錄中找不到 *.BND 檔案
- **THEN** 系統 SHALL 記錄 error，整個 recipe import 中止
