## ADDED Requirements

### Requirement: Bootstrap shared MySQL schema before runtime operations
系統 SHALL 在 pipeline 或 web 執行任何資料庫讀寫前，確保共用的 `ksbody_*` MySQL schema 已存在。

#### Scenario: Bootstrap schema before pipeline startup
- **WHEN** 使用者執行 `python -m ksbody pipeline`
- **THEN** 系統 SHALL 在 watcher 與 pipeline 寫入資料前建立所有缺少的 `ksbody_*` 資料表與索引

#### Scenario: Bootstrap schema before web startup
- **WHEN** 使用者執行 `python -m ksbody web`
- **THEN** 系統 SHALL 在 API route 開始查詢或寫入前建立所有缺少的 `ksbody_*` 資料表與索引

#### Scenario: Bootstrap schema before multi-process startup
- **WHEN** 使用者執行 `python -m ksbody all`
- **THEN** 主程序 SHALL 在啟動 pipeline 與 web 子程序前先完成一次 shared schema bootstrap

### Requirement: Schema bootstrap is idempotent
共用 schema bootstrap SHALL 可安全重複執行，不覆寫既有資料。

#### Scenario: Existing tables already present
- **WHEN** 系統在目標 MySQL 中發現所需的 `ksbody_*` 資料表與索引已存在
- **THEN** bootstrap SHALL 成功返回且不刪除、不重建既有資料表內容

#### Scenario: Empty database on first deployment
- **WHEN** 目標 MySQL schema 為空且服務首次啟動
- **THEN** bootstrap SHALL 建立 `ksbody.db.schema` 定義的所有資料表與索引，讓後續服務可直接運作
