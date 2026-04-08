## ADDED Requirements

### Requirement: Recognize timestamp-suffixed recipe body filenames
Watcher 模組 SHALL 將尾碼帶有 timestamp 的 recipe body 檔名視為有效輸入，且與既有檔名格式同等處理。

#### Scenario: Watcher event accepts timestamp suffix
- **WHEN** SMB 子資料夾中出現檔名 `L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1_1775539396`
- **THEN** watcher SHALL 將其識別為 recipe body 檔案並進入 debounce 與 pipeline callback 流程

#### Scenario: Full scan counts timestamp-suffixed files
- **WHEN** full scanner 遞迴掃描監控路徑
- **THEN** 系統 SHALL 將符合 `..._<recipe_version>_<timestamp>` 的檔案納入掃描、狀態統計與已處理判定

#### Scenario: Watcher file browser lists timestamp-suffixed files
- **WHEN** Web API 掃描 watcher files/status
- **THEN** 系統 SHALL 將 timestamp 尾碼 recipe body 檔案計入 `file_count` 並列入檔案清單
