## ADDED Requirements

### Requirement: Parse key-value parameter files
系統 SHALL 解析 PHY、PRM、LF、MAG 格式的檔案。這些檔案使用 `symbol = value units sys_type parm_type class min max default prc_min prc_max` 的 tabular 格式。

#### Scenario: Parse tabular parameter line
- **WHEN** 遇到行 `Bond1_Force = 25.0 grams VAR_E B1_PRM FULL 10.0 50.0 25.0 10.0 50.0`
- **THEN** 提取 param_name = "Bond1_Force"，param_value = "25.0"，unit = "grams"，min_value = "10.0"，max_value = "50.0"，default_value = "25.0"

#### Scenario: Parse simple key-value line
- **WHEN** 遇到行 `configurable_contact_detect	NO`（tab 分隔的簡單 key-value）
- **THEN** 提取 param_name = "configurable_contact_detect"，param_value = "NO"，unit/min/max/default 為 NULL

#### Scenario: Skip comment and blank lines
- **WHEN** 遇到以 `#` 開頭的行或空白行
- **THEN** 系統 SHALL 跳過該行

### Requirement: Parse sectioned files
系統 SHALL 解析 BND、REF、HB、WIR、BSG、AIC 等含有 section/block 結構的檔案。Block 以 `{` 開始 `}` 結束，或使用 tab 縮排。

#### Scenario: Parse BND machine data section
- **WHEN** BND 檔案包含 `mc_serial_number 10626` 格式的行
- **THEN** 提取為 param_name = "mc_serial_number"，param_value = "10626"

#### Scenario: Parse nested block
- **WHEN** 遇到 `ball_group 1 { ... }` 格式的巢狀結構
- **THEN** 使用 `{parent}.{child}` 格式組合參數名，如 `ball_group_1.pbi_dia_nom = 5.0`

#### Scenario: Parse WIR connect entries
- **WHEN** WIR 檔案包含 `connect 1 mdref_1 4 1 ConnX_1_Loop` 的連線定義
- **THEN** 提取為結構化記錄，包含 id、instance、site、group、profile

### Requirement: Parse APP file
系統 SHALL 解析 APP 檔案中的耗材規格資訊，產出結構化的 Capillary 和 Wire 資料。

#### Scenario: Parse capillary and wire specs
- **WHEN** APP 檔案包含 `TipDia=8.9`、`WireDia=1.7`、`WireMetal=3` 等
- **THEN** 提取所有耗材欄位，寫入 recipe_app_spec 寬表

### Requirement: Parse AID file as CSV
系統 SHALL 解析 AID 檔案，該檔案為 CSV 格式的 Auto Inspection 量測項目定義。

#### Scenario: Parse AID measurement definitions
- **WHEN** AID 檔案包含 `Ball Diameter (XY Avg),um,,,,,,,,,,,,`
- **THEN** 提取量測項目名稱和單位，存入 recipe_params

### Requirement: Parse RPM SQLite database
系統 SHALL 讀取 RPM 檔案（SQLite 格式），提取 rpm_limits 和 rpm_reference_data 表的資料。

#### Scenario: Extract RPM limits
- **WHEN** RPM SQLite 包含 rpm_limits_old 或類似限值表
- **THEN** 提取所有限值記錄（signal_name, property_name, lower_limit, upper_limit, active），寫入 recipe_rpm_limits

#### Scenario: Extract RPM reference data
- **WHEN** RPM SQLite 包含 rpm_reference_data 表
- **THEN** 提取統計資料（average, median, std_dev, min, max, sample_count），寫入 recipe_rpm_reference

#### Scenario: RPM file not present
- **WHEN** 解壓目錄中不存在 *.RPM 檔案
- **THEN** 系統 SHALL 跳過 RPM 解析，不報錯

### Requirement: Parse LHM and VHM files
系統 SHALL 解析 LHM（Loop Height Monitor）和 VHM（Vertical Height Monitor）配置檔。

#### Scenario: Parse monitor settings
- **WHEN** LHM 檔案包含 `enable = 0`、`interval = 1`、`loop_id 1 { ... }` 等
- **THEN** 提取所有監控設定參數，以 `{section}.{key}` 格式存入 recipe_params

### Requirement: Handle unknown or binary files gracefully
系統 SHALL 對無法解析的檔案（如 OTH 二進位檔、JPG 圖片）記錄日誌但不中斷解析流程。

#### Scenario: Binary file encountered
- **WHEN** 遇到 OTH 或其他無法解析的二進位檔案
- **THEN** 系統 SHALL 記錄檔名到日誌，跳過該檔案，繼續解析其他檔案

#### Scenario: AID file skipped for params storage
- **WHEN** 遇到 AID 檔案
- **THEN** 系統 SHALL 解析但不寫入 recipe_params（見「AID files shall not produce recipe_params entries」）

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

### Requirement: Prefix component params with semantic role
系統 SHALL 在儲存 PHY、PRM、REF 等 component 參數時，使用從 BND ComponentRegistry 解析出的語意角色作為 `param_name` 前綴，格式為 `<role>/<param_name>`。

**角色前綴規則**：
- `PHY`（mag_handler）→ `mag_handler/<param_name>`
- `PHY`（workholder）→ `workholder/<param_name>`
- `PRM`（第一個 parms，通常含 BSG）→ `parms/<param_name>`
- `PRM`（第二個 parms，有差異時保留）→ `parms_2/<param_name>`
- `REF`（DIE type）→ `die_ref/<param_name>`
- `REF`（LEAD type）→ `lead_ref/<param_name>`
- `LF`、`MAG`、`HB`、`IRS` → 不加前綴（每個 PP 唯一）

#### Scenario: mag_handler PHY params prefixed with role
- **WHEN** BND 宣告 `mag_handler CJ621A20.PHY`，且解析 `CJ621A20.PHY` 的參數 `IN_FIRST_SLOT = 1`
- **THEN** 系統 SHALL 將 param_name 儲存為 `mag_handler/IN_FIRST_SLOT`，而非 `CJ621A20/IN_FIRST_SLOT`

#### Scenario: workholder PHY params prefixed with role
- **WHEN** BND 宣告 `workholder CJ621A41.PHY`，且解析參數 `LOT_SEP_MODES = 0`
- **THEN** 系統 SHALL 將 param_name 儲存為 `workholder/LOT_SEP_MODES`

#### Scenario: PRM params prefixed with parms
- **WHEN** 第一個 `parms` 宣告的 PRM 包含參數 `Bond1_Force_Seg_01 = 150`
- **THEN** 系統 SHALL 儲存 `parms/Bond1_Force_Seg_01`

#### Scenario: Unique component files stored without prefix
- **WHEN** 解析 `CJ621A20.LF` 中的參數 `LF_PITCH = 254.0`
- **THEN** 系統 SHALL 儲存 `LF_PITCH`（無前綴），`file_type = "LF"`

#### Scenario: REF params prefixed by ref_type
- **WHEN** `AP643419.REF` 的 `ref_type = DIE`，包含參數 `num_sites = 4`
- **THEN** 系統 SHALL 儲存 `die_ref/num_sites`

### Requirement: BSG-aware parms_2 deduplication
系統 SHALL 在 recipe 含有多個 `parms` 宣告時，根據 BSG 存在差異和參數值差異決定是否保留第二組 PRM。

#### Scenario: Two PRM with BSG difference — keep both
- **WHEN** `parms[0]` 有 BSG、`parms[1]` 無 BSG，且兩者所有 param_value 相同
- **THEN** 系統 SHALL 兩者都儲存：`parms/<param>` 和 `parms_2/<param>`

#### Scenario: Two PRM identical in both BSG and values — merge
- **WHEN** `parms[0]` 和 `parms[1]` 的 has_bsg 相同，且所有 param_value 完全一致
- **THEN** 系統 SHALL 只儲存 `parms/<param>`，丟棄第二組

#### Scenario: Single parms — no suffix
- **WHEN** BND 只有一個 `parms` 宣告
- **THEN** 系統 SHALL 使用 `parms/<param>` 前綴，不帶數字後綴
