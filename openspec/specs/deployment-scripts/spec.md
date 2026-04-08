## ADDED Requirements

### Requirement: Deployment script for 1panel
系統 SHALL 提供 `scripts/deploy.sh`，一鍵完成前端 build、後端安裝、服務啟動。

#### Scenario: Full deployment
- **WHEN** 運維人員在 1panel 虛擬主機上執行 `bash scripts/deploy.sh`
- **THEN** 腳本 SHALL 依序執行：建立 virtualenv（若不存在）、`pip install .`、前端 `npm ci && npm run build`、啟動 `python -m ksbody all`

#### Scenario: Frontend build output location
- **WHEN** 前端 build 完成
- **THEN** build 產物位於 `ksbody/web/frontend/dist/`，FastAPI 直接 serve 該目錄

#### Scenario: Deploy script is idempotent
- **WHEN** 重複執行 `deploy.sh`
- **THEN** 腳本 SHALL 安全地重新安裝依賴並重啟服務，不產生殘留 process

### Requirement: pyproject.toml as dependency source
系統 SHALL 使用 `pyproject.toml` 管理所有 Python 依賴，取代 `requirements.txt`。

#### Scenario: Install all dependencies
- **WHEN** 執行 `pip install .`
- **THEN** 安裝 watchdog、sqlalchemy、pymysql、python-dotenv、fastapi、uvicorn、pydantic 等所有必要依賴

#### Scenario: Optional Oracle dependency
- **WHEN** 執行 `pip install ".[oracle]"`
- **THEN** 額外安裝 `oracledb` 套件

#### Scenario: Development install
- **WHEN** 開發者執行 `pip install -e .`
- **THEN** 以 editable 模式安裝，程式碼變更即時生效
