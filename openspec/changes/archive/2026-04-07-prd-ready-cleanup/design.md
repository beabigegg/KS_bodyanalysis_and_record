## Context

專案目前由兩個獨立服務組成：
1. **Pipeline 服務**（`main.py`）— 監控 SMB 路徑、解析 recipe body、寫入 MySQL，透過 `config.yaml` 讀取設定
2. **Web 服務**（`web/app.py`）— FastAPI 後端 + React 前端（已整合為單體式靜態託管），透過 `.env` 讀取設定

公司規範要求：禁止硬編碼敏感資訊、統一使用環境變數、版本鎖定、補齊四份文件、清理開發殘留。Web 服務已大致合規，Pipeline 服務是主要整頓對象。

## Goals / Non-Goals

**Goals:**
- Pipeline 設定從 config.yaml 遷移至 .env，消除硬編碼密碼
- 統一根目錄 `.env.example` 涵蓋 pipeline + web 全部設定
- 根目錄 requirements.txt 鎖定版本並加註說明
- 補齊 README.md（PRD / SDD / TDD 由 OpenSpec 開發紀錄涵蓋，不另建）
- 清理 legacy/、samples/、web/recipe.db、快取目錄
- .gitignore 補強至規範標準

**Non-Goals:**
- 不改動任何業務邏輯或 parser 實作
- 不合併 pipeline 與 web 為同一 process（兩者職責不同，分離是合理的）
- 不重構 web/settings.py（已合規）
- 不建立 CI/CD pipeline（非此次範圍）
- 不處理 EYE/IEY parser 待辦（獨立 change）

## Decisions

### D1: Pipeline 設定改用 .env + python-dotenv

**選擇**: 重寫 `config/settings.py`，從 `os.getenv()` 讀取所有設定，移除 pyyaml 依賴。

**替代方案**:
- A) 保留 YAML 但移除敏感欄位至 .env → 混用兩套設定機制，增加維護負擔
- B) 改用 pydantic-settings → 引入額外依賴，對此規模專案過度

**理由**: Web 端已採用 `python-dotenv` + `os.getenv()`，統一方式最簡單。config.yaml 中的非敏感設定（debounce、scan_interval 等）同樣搬入 .env，因為值很少且穩定。

### D2: 統一 .env.example 於根目錄

**選擇**: 根目錄放置單一 `.env.example`，涵蓋 pipeline 和 web 全部變數。移除 `web/.env.example`。

**理由**: `web/settings.py` 已有 fallback 機制（先讀 web/.env 再讀根 .env），統一後部署只需管理一份。

### D3: requirements.txt 合併策略

**選擇**: 保留兩份 requirements.txt（根目錄 for pipeline、web/ for web），各自鎖定版本。共用的套件（sqlalchemy、pymysql）在兩份中各自聲明。

**替代方案**: 合併為一份 → pipeline 不需要 fastapi/uvicorn，web 不需要 watchdog，強制合併會拉入不必要依賴。

**理由**: 兩個服務的依賴集不同，分開管理更清晰，部署時各裝各的。

### D4: legacy/ 和 samples/ 直接刪除

**選擇**: 用 `git rm -r` 從追蹤中移除，不保留任何替代。

**理由**: legacy/ 只有一個已棄用的舊腳本，git history 中可追溯。samples/ 是測試用範例資料，不應進 repo。

### D5: 僅建立 README.md

**選擇**: 建立 README.md 並填入完整資訊。PRD / SDD / TDD 不另建，因為 OpenSpec 開發紀錄（specs/、changes/）已涵蓋這些文件的功能。

**理由**: 避免重複維護，OpenSpec 的 proposal + specs + design 已提供需求、設計、測試規格。

## Risks / Trade-offs

- **[Breaking config]** Pipeline 啟動方式改變（不再需要 --config 參數），現有部署腳本需同步更新 → **Mitigation**: 在 README 中明確說明新啟動方式，保留 --config 參數但改為可選（向下相容過渡期）
- **[資料遺失]** 刪除 samples/ 和 legacy/ 不可逆 → **Mitigation**: 這些檔案已在 git history 中，且確認無其他模組引用
- **[.env 安全]** .env 檔案若被意外 commit → **Mitigation**: .gitignore 已有 .env 排除規則，且 config.yaml 也已排除

## Migration Plan

1. 建立根目錄 `.env.example`（合併 pipeline + web 變數）
2. 重寫 `config/settings.py` 改讀 .env
3. 更新 `main.py` 移除 --config 預設值，改為可選
4. 鎖定根目錄 `requirements.txt` 版本，新增 python-dotenv
5. `git rm -r legacy/ samples/ web/recipe.db`
6. 更新 `.gitignore`
7. 建立四份文件骨架
8. 移除 `config.yaml.example`、`web/.env.example`（統一至根目錄）
9. 驗證：`python main.py --help` 和 `cd web && python app.py` 皆可啟動

## Open Questions

- Pipeline 和 Web 的 MySQL 設定是否永遠指向同一台？如果是，.env 中只需一組 `MYSQL_*` 變數即可。（假設：是，統一使用同一組）
