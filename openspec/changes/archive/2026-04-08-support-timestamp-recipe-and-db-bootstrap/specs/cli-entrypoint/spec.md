## MODIFIED Requirements

### Requirement: Unified CLI with subcommands
系統 SHALL 提供 `python -m ksbody` 作為統一入口，透過子命令選擇啟動模式，並在服務啟動路徑上先完成共用資料庫 schema bootstrap。

#### Scenario: Run pipeline only
- **WHEN** 使用者執行 `python -m ksbody pipeline`
- **THEN** 系統先完成 shared schema bootstrap，再啟動 watcher + scanner + pipeline 服務

#### Scenario: Run web only
- **WHEN** 使用者執行 `python -m ksbody web`
- **THEN** 系統先完成 shared schema bootstrap，再啟動 FastAPI + uvicorn 服務

#### Scenario: Run all services
- **WHEN** 使用者執行 `python -m ksbody all`
- **THEN** 系統透過 `ProcessManager` 同時啟動 pipeline 和 web 兩個子 process，且主程序 SHALL 在啟動子 process 前先完成 shared schema bootstrap

#### Scenario: Initialize database
- **WHEN** 使用者執行 `python -m ksbody init-db`
- **THEN** 系統建立所有資料庫 table schema 後退出

#### Scenario: Process single file
- **WHEN** 使用者執行 `python -m ksbody pipeline --process-file <path>`
- **THEN** 系統先完成 shared schema bootstrap，再處理指定的單一 recipe body 檔案後退出（用於驗證）

#### Scenario: No subcommand
- **WHEN** 使用者執行 `python -m ksbody` 不帶子命令
- **THEN** 系統 SHALL 顯示使用說明（help）
