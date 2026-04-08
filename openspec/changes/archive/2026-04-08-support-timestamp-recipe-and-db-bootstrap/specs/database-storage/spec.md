## ADDED Requirements

### Requirement: Shared physical table names use ksbody prefix
系統 SHALL 使用 `ksbody.db.schema` 中定義的 `ksbody_*` 實體表作為 pipeline 與 web 共用的 MySQL schema。

#### Scenario: Shared schema names are used for import data
- **WHEN** pipeline 寫入 recipe import 與 parameter 資料
- **THEN** 系統 SHALL 寫入 `ksbody_recipe_import`、`ksbody_recipe_params` 與其他 `ksbody_*` 對應表，而非無前綴的舊表名

#### Scenario: Shared schema names are used for watcher data
- **WHEN** web 或 pipeline 寫入 watcher event、reparse task 與 cleanup 資料
- **THEN** 系統 SHALL 使用 `ksbody_watcher_events`、`ksbody_reparse_tasks`、`ksbody_cleanup_config`、`ksbody_cleanup_log`
