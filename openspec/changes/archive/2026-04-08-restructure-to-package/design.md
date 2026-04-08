## Context

KS Body Analysis 專案由兩個獨立服務組成：Pipeline（檔案監控→解析→入庫）和 Web（FastAPI API + React 前端）。目前它們共用同一個 git repo 但各自有獨立的設定系統和啟動方式。Web 透過 `sys.path` hack 存取上層的 `db/schema.py`。部署目標是 1panel 虛擬主機（Linux），前後端跑在同一台機器上。

現有模組依賴關係：
- `main.py` → `config.settings`, `db.*`, `pipeline`, `watcher.*`
- `pipeline.py` → `db.repository`, `extractor.*`, `parsers.*`
- `web/app.py` → `web/settings`, `web/routes/*`, `web/deps` → (sys.path hack) → `db.schema`

## Goals / Non-Goals

**Goals:**
- 將所有 Python 模組統一到 `ksbody` package 下，消除 sys.path hack
- 合併兩套設定為單一來源
- 提供 `python -m ksbody {pipeline|web|all|init-db}` 統一入口
- `all` 模式下透過 ProcessManager 管理子 process，含健康偵測與自動重啟
- 使用 `pyproject.toml` 管理完整依賴，支援 `pip install -e .` 開發
- 清理 git 歷史中的明文密碼

**Non-Goals:**
- 不做 Docker 化（1panel 自行管理虛擬環境）
- 不改動業務邏輯（parser、pipeline、route handler 的行為不變）
- 不改動前端程式碼（React/Vite 的 src/ 不動，僅搬移目錄位置）
- 不做 monorepo 拆分（pipeline 和 web 不分成獨立 package）

## Decisions

### 1. Package 命名與結構

**決定**：頂層 package 名稱為 `ksbody`，所有模組移入其下。

```
ksbody/
├── __init__.py
├── __main__.py
├── config.py
├── manager.py
├── db/
├── pipeline/
│   ├── __init__.py      ← RecipePipeline (原 pipeline.py)
│   ├── runner.py        ← 原 main.py 的 pipeline 啟動邏輯
│   ├── extractor/
│   └── parsers/
├── watcher/
└── web/
    ├── app.py
    ├── deps.py
    ├── routes/
    ├── services/
    ├── utils/
    └── frontend/
```

**替代方案**：保持扁平結構（`ksbody/extractor/`, `ksbody/parsers/`），不建子 package。
**取捨**：`extractor` 和 `parsers` 只被 pipeline 使用，放在 `ksbody.pipeline` 下更符合依賴方向。扁平結構雖然 import 路徑短，但會模糊模組間的隸屬關係。

### 2. 統一設定架構

**決定**：單一 `ksbody/config.py`，匯出一個 `Settings` dataclass，內含所有設定（pipeline + web）。使用 `functools.lru_cache` 確保全域單例。

```python
@dataclass(frozen=True)
class Settings:
    # Shared
    mysql: MySQLConfig
    # Pipeline-only
    watch_paths: list[Path]
    debounce: DebounceConfig
    scan_interval: int
    log_file: Path
    state_file: Path
    # Web-only
    app_host: str
    app_port: int
    app_mode: str
    app_cors_origins: list[str]
    oracle: OracleConfig | None
    debug: bool

@lru_cache(maxsize=1)
def get_settings() -> Settings: ...
```

**替代方案**：分成 `PipelineSettings` 和 `WebSettings` 兩個 class。
**取捨**：分開設定在單獨啟動時可以避免驗證不相關的 env var（例如跑 web 時不需要 WATCH_PATHS）。但我們的主要使用模式是 `all`（兩者同時跑），而且 `.env` 本來就包含所有設定。統一 class 更簡單，pipeline-only 和 web-only 的欄位給予合理預設值即可。

### 3. ProcessManager 設計

**決定**：`ksbody/manager.py` 實作 `ProcessManager` class，使用 `multiprocessing.Process` 管理子 process。

核心行為：
- 主 process 啟動後 fork 兩個子 process（pipeline 和 web）
- 健康檢查迴圈每 10 秒執行一次
- Pipeline 健康：`Process.is_alive()` 檢查
- Web 健康：`Process.is_alive()` + HTTP `GET /api/health`（每 30 秒，啟動後 grace period 15 秒）
- 子 process 死亡時自動重啟，記錄 exit code
- 連續失敗超過 `max_restarts`（預設 5 次）停止重啟，log CRITICAL
- 重啟間隔指數退避：`min(base * 2^n, max_interval)`，預設 base=2s, max=60s
- SIGTERM/SIGINT 優雅關閉：送 SIGTERM 給子 process，等待 timeout 後 SIGKILL

**替代方案**：使用 supervisor/systemd 管理兩個獨立 process。
**取捨**：外部 process manager 更成熟，但增加部署依賴。1panel 已經是上層管理者，內建 ProcessManager 讓 1panel 只需管理一個 process，簡化設定。如果未來需要更強的 process 管理，可以拆成兩個 1panel 任務。

### 4. Import 路徑遷移策略

**決定**：一次性全面修改所有 import 路徑，不做漸進式遷移。

遷移對照表（關鍵變更）：
| 原路徑 | 新路徑 |
|--------|--------|
| `config.settings` | `ksbody.config` |
| `db.repository` | `ksbody.db.repository` |
| `db.schema` | `ksbody.db.schema` |
| `pipeline` | `ksbody.pipeline` |
| `parsers.*` | `ksbody.pipeline.parsers.*` |
| `extractor.*` | `ksbody.pipeline.extractor.*` |
| `watcher.*` | `ksbody.watcher.*` |
| `settings` (web) | `ksbody.config` |
| `deps` (web) | `ksbody.web.deps` |
| `routes.*` (web) | `ksbody.web.routes.*` |
| `services.*` (web) | `ksbody.web.services.*` |
| `utils.*` (web) | `ksbody.web.utils.*` |

**取捨**：一次改完動靜大但乾淨，不會有新舊路徑混用的過渡期。既然只有一人開發，無需考慮並行開發的相容性。

### 5. pyproject.toml 依賴管理

**決定**：使用 `pyproject.toml` 搭配 setuptools backend。

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "ksbody"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "watchdog>=4.0",
    "sqlalchemy>=2.0",
    "pymysql>=1.1",
    "python-dotenv>=1.0",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "pydantic>=2.0",
]

[project.optional-dependencies]
oracle = ["oracledb>=2.0"]

[project.scripts]
ksbody = "ksbody.__main__:main"
```

### 6. 前端靜態檔案位置

**決定**：`web/frontend/` 整個搬入 `ksbody/web/frontend/`。`app.py` 中 `FRONTEND_DIST` 路徑指向 `ksbody/web/frontend/dist/`。

`pyproject.toml` 中透過 `[tool.setuptools.package-data]` 包含 `dist/**` 確保 build 產物隨 package 安裝。前端的 `vite.config` 中 API proxy 不需要改（仍是 `/api/*` → localhost）。

### 7. Git 歷史清理

**決定**：使用 `git filter-repo --path config.yaml --invert-paths` 從所有 commit 中移除 `config.yaml`。

執行時機：在 package 重構完成並確認可運行之後，作為最後一步執行。這樣避免在重構過程中處理 rewrite 後的歷史。

## Risks / Trade-offs

- **[大量 import 改動]** → 一次改 30+ 檔案的 import，容易遺漏。**緩解**：改完後跑全部測試 + `python -m ksbody pipeline --process-file <test-file>` 驗證 pipeline，`python -m ksbody web` 驗證 web 啟動。
- **[ProcessManager 複雜度]** → 自建 process manager 不如 systemd 成熟。**緩解**：保持簡單（只做 alive check + HTTP health），不做 log aggregation 或 resource monitoring。如果不穩定可以隨時退回 1panel 分開管理。
- **[前端路徑變更]** → 搬移 `frontend/` 後 npm workspace 或 CI 路徑可能壞掉。**緩解**：前端是獨立的 Vite 專案，只要 `package.json` 在正確位置就能 build。
- **[git filter-repo]** → 重寫歷史後所有 commit hash 改變。**緩解**：僅一人開發，無影響。執行前備份。
