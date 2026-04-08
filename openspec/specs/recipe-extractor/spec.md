## ADDED Requirements

### Requirement: Extract metadata from file path
系統 SHALL 從檔案的完整路徑中提取 metadata：machine_type 來自第一層資料夾名，machine_id 來自第二層資料夾名。

#### Scenario: Parse path for machine info
- **WHEN** 收到路徑 `{root}/WBK_ConneX Elite_EAP/GWBK-0270/L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1`
- **THEN** 提取 machine_type = "WBK_ConneX Elite_EAP"，machine_id = "GWBK-0270"

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

### Requirement: Decompress gzip tar archive
系統 SHALL 將 recipe body 檔案（gzip tar 格式）解壓到暫存目錄。

#### Scenario: Successful decompression
- **WHEN** 收到有效的 gzip tar 檔案
- **THEN** 解壓所有檔案到暫存目錄，回傳暫存目錄路徑

#### Scenario: Cleanup temp directory
- **WHEN** 解析流程完成（成功或失敗）
- **THEN** 系統 SHALL 刪除暫存目錄及其所有內容

### Requirement: Extract BND metadata
系統 SHALL 從解壓後的 BND 檔案中提取 recipe 級別的 metadata：recipe_name、mc_serial_number、mc_software_version、date_time、mc_model、workholder 等。

#### Scenario: Parse BND header fields
- **WHEN** 解壓目錄中存在 `*.BND` 檔案
- **THEN** 提取 name、mc_serial_number、mc_software_version、date_time 等欄位，合併入 metadata
