## Why

目前 SMB 路徑上的 recipe body 檔名已包含尾碼 timestamp，例如 `..._1_1775539423`，但 watcher 與 metadata parser 仍只接受 `..._1` 的舊格式，導致遞迴掃描雖有找到檔案，卻在檔名過濾階段直接略過。另一路徑上，服務啟動前若未手動執行資料庫初始化，MySQL 缺少 `ksbody_*` 資料表時會使 watcher event、import 與後續 API 全部失效。

## What Changes

- 放寬 recipe body 檔名規則，支援既有 `..._<recipe_version>` 格式與新式 `..._<recipe_version>_<timestamp>` 格式。
- 更新 recipe metadata 解析行為，允許存在尾碼 timestamp，同時維持既有 `recipe_version` 萃取結果不變。
- 修正 watcher 與 watcher file browser 的 recipe 檔案判定邏輯，使 SMB 子資料夾中的 timestamp 尾碼檔案可被列入掃描、狀態統計與檔案列表。
- 補齊資料庫 bootstrap 要求，確保 pipeline / web 啟動或 `ksbody all` 啟動路徑上，所需的 `ksbody_*` MySQL 資料表會在首次執行時建立。
- 更新初始化與部署文件，明確說明 schema 建立責任與驗證方式。

## Capabilities

### New Capabilities
- `database-bootstrap`: 定義服務啟動時自動確保共用 MySQL schema 存在的行為。

### Modified Capabilities
- `folder-watcher`: watcher 對 recipe body 的檔名辨識需支援 timestamp 尾碼格式。
- `recipe-extractor`: 檔名 metadata 解析需支援 timestamp 尾碼格式。
- `database-storage`: 明確要求使用 `ksbody_*` 共用資料表並保證初始化後可供 pipeline 與 web 共用。
- `cli-entrypoint`: `ksbody all` 與服務啟動路徑需在子服務開始前完成資料庫 bootstrap。
- `project-docs`: README 需更新新的檔名格式與資料庫初始化說明。

## Impact

- Affected code: `ksbody/watcher/handler.py`, `ksbody/pipeline/extractor/metadata.py`, `ksbody/pipeline/runner.py`, `ksbody/web/routes/watcher.py`, `ksbody/db/init_db.py`, `ksbody/manager.py`, `README.md`
- Affected systems: SMB recipe ingestion flow, MySQL schema bootstrap, watcher dashboard/file browser visibility
- Risk areas: 舊格式檔名相容性、服務啟動順序、首次連線 MySQL 時的 schema 建立權限
