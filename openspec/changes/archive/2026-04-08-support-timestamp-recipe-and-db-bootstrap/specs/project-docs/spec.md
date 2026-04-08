## ADDED Requirements

### Requirement: README documents timestamp filename contract
README.md SHALL 說明 recipe body 檔名支援標準版本格式與附加 timestamp 尾碼格式。

#### Scenario: Developer verifies accepted filename patterns
- **WHEN** 開發者查閱 README 的 watcher / pipeline 說明
- **THEN** 文件 SHALL 列出 `..._<recipe_version>` 與 `..._<recipe_version>_<timestamp>` 兩種可接受格式

### Requirement: README documents database bootstrap behavior
README.md SHALL 說明服務啟動與 `init-db` 對 MySQL schema 的責任分工與驗證方式。

#### Scenario: Developer deploys on empty database
- **WHEN** 開發者在空的 MySQL schema 上部署服務
- **THEN** README SHALL 說明服務啟動會自動建立缺少的 `ksbody_*` 資料表，並提供驗證指令
