## ADDED Requirements

### Requirement: Prefix die-specific param names with die code
系統 SHALL 在儲存 die 專屬參數時，將 die 代碼作為前綴加入 `param_name`，格式為 `<die_code>/<param_name>`。

**Die 專屬 file_type**：PHY、PRM、LF、MAG、REF（檔名以 die 代碼開頭，如 `CJ621A20.PRM`）
**機台共用 file_type**：BND、APP、BSG、AIC、LHM、VHM、PPC、RPM、AID（不加前綴）

#### Scenario: Store die-specific param with die code prefix
- **WHEN** 解析 `CJ621A20.PRM` 中的參數 `Bond1_Force_Seg_01 = 150`
- **THEN** 系統 SHALL 將 param_name 儲存為 `CJ621A20/Bond1_Force_Seg_01`
- **AND** file_type 仍為 `PRM`

#### Scenario: Machine-level file params stored without prefix
- **WHEN** 解析 `MR192600.BND` 中的參數 `mc_serial_number = 17620`
- **THEN** 系統 SHALL 將 param_name 儲存為 `mc_serial_number`（無前綴）

#### Scenario: Die code extracted from file stem
- **WHEN** pipeline 處理副檔名屬於 die 專屬 file_type 的檔案
- **THEN** die 代碼 SHALL 從檔名主幹（stem）提取，規則為 `Path(file_path).stem`（如 `CJ621A20.PRM` → `CJ621A20`）

### Requirement: AID files shall not produce recipe_params entries
系統 SHALL 在 import pipeline 中不將 AID 檔案的解析結果寫入 `recipe_params`。

**理由**：AID 為 Auto Inspection 量測項目定義清單，僅含項目名稱與單位，無數值，不具比較意義。

#### Scenario: AID parsed but params discarded
- **WHEN** pipeline 解析到 AID 檔案
- **THEN** CsvParser 解析動作仍可執行（向後相容）
- **AND** pipeline SHALL 丟棄 AID 產生的所有 params，不寫入 `recipe_params`

#### Scenario: AID parsing failure does not break import
- **WHEN** AID 檔案格式異常或缺失
- **THEN** 系統 SHALL 記錄警告並繼續處理其他檔案，不中斷整體 import 流程

## MODIFIED Requirements

### Requirement: Handle unknown or binary files gracefully
系統 SHALL 對無法解析的檔案（如 OTH 二進位檔、JPG 圖片）記錄日誌但不中斷解析流程。

#### Scenario: Binary file encountered
- **WHEN** 遇到 OTH 或其他無法解析的二進位檔案
- **THEN** 系統 SHALL 記錄檔名到日誌，跳過該檔案，繼續解析其他檔案

#### Scenario: AID file skipped for params storage
- **WHEN** 遇到 AID 檔案
- **THEN** 系統 SHALL 解析但不寫入 recipe_params（見「AID files shall not produce recipe_params entries」）
