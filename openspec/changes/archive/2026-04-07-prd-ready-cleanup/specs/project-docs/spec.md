## ADDED Requirements

### Requirement: README.md at project root
專案根目錄 SHALL 提供 README.md，包含：專案介紹、系統架構簡述、安裝方式、環境變數說明、啟動指令、使用方式、佈署說明。

#### Scenario: Developer reads README for setup
- **WHEN** 新開發者 clone 專案
- **THEN** README.md 提供從安裝依賴到啟動服務的完整步驟

#### Scenario: README covers both services
- **WHEN** 查閱 README.md
- **THEN** 文件分別說明 pipeline 服務和 web 服務的啟動方式與用途

### Requirement: Version-pinned requirements.txt
根目錄 `requirements.txt` SHALL 使用 `==` 鎖定所有套件版本，並以 `#` 註解說明每個套件的用途。

#### Scenario: All packages pinned
- **WHEN** 檢查根目錄 `requirements.txt`
- **THEN** 每個套件行格式為 `package==x.y.z  # 用途說明`，無 `>=` 或無版本的條目

### Requirement: Clean .gitignore
`.gitignore` SHALL 涵蓋規範要求的所有排除項目。

#### Scenario: All required exclusions present
- **WHEN** 檢查 `.gitignore`
- **THEN** 包含 `.env`、`node_modules/`、`__pycache__/`、`*.pyc`、`*.pyo`、`venv/`、`dist/`、`build/`、`*.log`、`logs/`、`uploads/`、`outputs/`、`tmp/`、`temp/`、`nul`、`.vscode/`、`.idea/`、`.DS_Store`、`*.db`、`*.sqlite3`

### Requirement: No legacy or sample data in repo
專案 SHALL 不追蹤已棄用的程式碼或測試用範例資料。

#### Scenario: legacy/ removed
- **WHEN** 檢查 repo 內容
- **THEN** `legacy/` 目錄不存在於追蹤檔案中

#### Scenario: samples/ removed
- **WHEN** 檢查 repo 內容
- **THEN** `samples/` 目錄不存在於追蹤檔案中

#### Scenario: SQLite database not tracked
- **WHEN** 檢查 repo 內容
- **THEN** `web/recipe.db` 不存在於追蹤檔案中
