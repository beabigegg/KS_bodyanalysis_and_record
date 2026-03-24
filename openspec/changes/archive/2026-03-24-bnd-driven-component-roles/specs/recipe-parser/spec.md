## MODIFIED Requirements

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

**替換前一版的「die 代碼前綴」規則**（原 `fix-compare-and-extraction-gaps` 定義的 `DIE_SPECIFIC_FILE_TYPES` 方案）。

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
