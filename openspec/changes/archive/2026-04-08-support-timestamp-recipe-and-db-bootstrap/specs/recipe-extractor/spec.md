## MODIFIED Requirements

### Requirement: Extract metadata from filename
系統 SHALL 從 recipe body 檔名中解析出 product_type、bop、wafer_pn、recipe_version，並允許版本號後方帶有可選的 timestamp 尾碼。

#### Scenario: Parse standard filename
- **WHEN** 檔名為 `L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1`
- **THEN** 提取 product_type = "PJS6400"，bop = "ECC17"，wafer_pn = "WAF007957"，recipe_version = 1

#### Scenario: Parse filename with timestamp suffix
- **WHEN** 檔名為 `L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1_1775539396`
- **THEN** 系統 SHALL 提取 product_type = "PJS6400"，bop = "ECC17"，wafer_pn = "WAF007957"，recipe_version = 1，且忽略 timestamp 尾碼不入 metadata

#### Scenario: Filename with different machine type prefix
- **WHEN** 檔名前綴不同（如其他機型）但仍以 `@` 分隔欄位，並以 `_` 接版本號或 `版本號_timestamp`
- **THEN** 系統 SHALL 正確解析 `@` 分隔的各欄位與 recipe_version
