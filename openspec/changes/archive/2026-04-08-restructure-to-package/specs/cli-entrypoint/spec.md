## ADDED Requirements

### Requirement: Unified CLI with subcommands
系統 SHALL 提供 `python -m ksbody` 作為統一入口，透過子命令選擇啟動模式。

#### Scenario: Run pipeline only
- **WHEN** 使用者執行 `python -m ksbody pipeline`
- **THEN** 系統啟動 watcher + scanner + pipeline 服務，行為等同原本的 `python main.py`

#### Scenario: Run web only
- **WHEN** 使用者執行 `python -m ksbody web`
- **THEN** 系統啟動 FastAPI + uvicorn 服務，行為等同原本的 `cd web && python app.py`

#### Scenario: Run all services
- **WHEN** 使用者執行 `python -m ksbody all`
- **THEN** 系統透過 `ProcessManager` 同時啟動 pipeline 和 web 兩個子 process

#### Scenario: Initialize database
- **WHEN** 使用者執行 `python -m ksbody init-db`
- **THEN** 系統建立所有資料庫 table schema 後退出

#### Scenario: Process single file
- **WHEN** 使用者執行 `python -m ksbody pipeline --process-file <path>`
- **THEN** 系統處理指定的單一 recipe body 檔案後退出（用於驗證）

#### Scenario: No subcommand
- **WHEN** 使用者執行 `python -m ksbody` 不帶子命令
- **THEN** 系統 SHALL 顯示使用說明（help）

### Requirement: Console script entrypoint
系統 SHALL 透過 `pyproject.toml` 註冊 `ksbody` 命令，使 `pip install` 後可直接使用。

#### Scenario: Use ksbody command after install
- **WHEN** 使用者執行 `pip install .` 後
- **THEN** `ksbody all`、`ksbody pipeline`、`ksbody web`、`ksbody init-db` 等命令可直接使用，行為等同 `python -m ksbody`
