### Requirement: Classify param_name into stage and category
系統 SHALL 提供 `ParamClassifier`，將 `param_name`（格式 `{role}/{pp_body}` 或無 role prefix 的裸名）靜態映射至 `(stage, category)` 元組。

#### Scenario: PRM prefix maps to stage
- **WHEN** `param_name = "parms/B1_Force_Seg_01"`（role = parms，PP body prefix = B1）
- **THEN** classifier SHALL 回傳 `stage = "bond1"`，`category = "seg_01"`

#### Scenario: PRM ball_formation prefix
- **WHEN** `param_name = "parms/EFO_Power"`（prefix = EFO）
- **THEN** classifier SHALL 回傳 `stage = "ball_formation"`，`category = "efo"`

#### Scenario: PRM loop balance prefix
- **WHEN** `param_name = "parms/Bal_Loop_Percent"`（prefix = Bal）
- **THEN** classifier SHALL 回傳 `stage = "loop"`，`category = "balance"`

#### Scenario: PHY mag_handler keyword mapping
- **WHEN** `param_name = "mag_handler/IN_FIRST_SLOT"`
- **THEN** classifier SHALL 回傳 `stage = None`，`category = "slot"`

#### Scenario: PHY workholder keyword mapping
- **WHEN** `param_name = "workholder/LOT_SEP_MODES"`
- **THEN** classifier SHALL 回傳 `stage = None`，`category = "indexing"`

#### Scenario: REF die_ref keyword mapping
- **WHEN** `param_name = "die_ref/eyepoint_x_1"`
- **THEN** classifier SHALL 回傳 `stage = None`，`category = "eyepoint"`

#### Scenario: REF lead_ref VLL category
- **WHEN** `param_name = "lead_ref/corridor_length"`
- **THEN** classifier SHALL 回傳 `stage = None`，`category = "vll"`

#### Scenario: LF and MAG remain unclassified
- **WHEN** `file_type` 為 `LF` 或 `MAG`
- **THEN** classifier SHALL 回傳 `stage = None`，`category = None`

#### Scenario: HB temperature zone mapping
- **WHEN** `param_name` 含有 `preheat` 關鍵字（大小寫不敏感）且 `file_type = "HB"`
- **THEN** classifier SHALL 回傳 `stage = None`，`category = "preheat"`

#### Scenario: Unknown prefix falls back to _unmapped
- **WHEN** PP body prefix 不在靜態映射表中（如 `XYZ_SomeParam`）
- **THEN** classifier SHALL 回傳 `stage = "_unmapped"`，`category = "xyz"`（prefix 小寫化）

#### Scenario: Equalization prefix falls back to _unmapped
- **WHEN** `param_name` 的 PP body prefix 為 `Equ`
- **THEN** classifier SHALL 回傳 `stage = "_unmapped"`，`category = "equalization"`

### Requirement: Segment number extraction for bond stages
系統 SHALL 從 bond1/bond2 的 PP body 中動態提取 segment 編號作為 category。

#### Scenario: Extract segment number
- **WHEN** PP body 含有 `_Seg_01`（大小寫不敏感）
- **THEN** classifier SHALL 回傳 `category = "seg_01"`

#### Scenario: No segment number falls back to misc
- **WHEN** PP body prefix 為 `B1` 但 pp_body 不含 `_Seg_` pattern（如 `B1_Contact_Level`）
- **THEN** classifier SHALL 回傳 `category = "misc"`
