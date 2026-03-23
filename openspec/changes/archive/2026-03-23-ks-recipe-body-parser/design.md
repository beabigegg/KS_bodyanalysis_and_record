## Context

目前 KS ConnX Elite 打線機的 recipe body 以 gzip tar 壓縮檔存放在網路共享路徑 `\\10.1.1.43\eap\prod\Recipe_Prod\`。現有 `ks_body_to_recipe.py` 僅能手動解壓還原。生產端需要自動化解析並儲存至 MySQL，以支援跨機台比較、時間序列追蹤和未來的 R2R 控制。

Recipe body 解壓後包含 15+ 種檔案格式，其中大部分為 key-value 或 tabular 文字檔，一個為 SQLite 資料庫 (RPM)，另有 JPG 圖片和少量二進位檔 (OTH)。

資料夾結構為三層：`{機型}_EAP / {machine_id} / {body檔案}`。

## Goals / Non-Goals

**Goals:**
- 監聽網路資料夾，自動偵測 recipe body 檔案變更並觸發解析
- 全參數解析所有文字格式的 recipe 檔案，結構化存入 MySQL
- 從路徑與檔名自動提取 metadata (machine_type, machine_id, product_type, bop, wafer_pn)
- 解析 RPM SQLite 資料庫，搬入 MySQL
- 預留 lot_id 接口供後續 MES 對接

**Non-Goals:**
- LOT ID 自動對接 MES/EAP（Phase 2）
- 良率資料匯入與分析（Phase 2）
- Run-to-Run 控制模組（Phase 3）
- 解析 JPG 圖片內容或 OTH 二進位檔
- Web UI 或 GUI 介面（本階段為背景服務）

## Decisions

### 1. 參數儲存策略：EAV 模式

**選擇**: Entity-Attribute-Value 模式儲存 recipe 參數

**替代方案**: 寬表（每個參數一個 column）

**理由**:
- PRM 檔有數百個參數，不同機型參數集不同，寬表會產生大量 NULL
- 新參數不需要 ALTER TABLE
- R2R 場景需要動態選取任意參數子集進行分析
- 查詢可透過 view 或應用層 pivot 解決

### 2. 混合表結構：EAV + 專用寬表

**選擇**: 核心參數用 EAV，結構固定的子集用寬表

**理由**:
- APP（耗材規格）、BSG（Ball Signature）欄位固定且經常獨立查詢，寬表更直觀
- RPM 資料本身已有 schema（來自 SQLite），直接映射到 MySQL 表
- EAV 處理所有 PHY/PRM/LF/MAG 等可變參數

### 3. 解析器架構：策略模式

**選擇**: 為每種檔案格式實作獨立的 parser class，統一介面

```
BaseParser (abstract)
├── KeyValueParser     → PHY, PRM, LF, MAG (symbol = value 格式)
├── SectionedParser    → BND, REF, HB, WIR, BSG, AIC (section/block 格式)
├── CsvParser          → AID
├── IniLikeParser      → APP, LHM, VHM, PPC (key=value 或 key value 格式)
└── SqliteParser       → RPM
```

**理由**:
- 檔案格式可歸類為 4-5 種 pattern，避免為每個副檔名寫獨立邏輯
- 統一介面方便後續擴展其他機型

### 4. 監聽機制：watchdog + debounce

**選擇**: 使用 Python watchdog 庫監聽資料夾，搭配 debounce 機制

**理由**:
- 檔案覆蓋寫入可能觸發多次事件（create → modify），需要 debounce 避免重複解析
- watchdog 支援遞迴監聽，適合三層目錄結構
- 網路路徑需要 polling observer（非 inotify），watchdog 的 PollingObserver 可處理

### 5. 資料庫連線：SQLAlchemy Core

**選擇**: SQLAlchemy Core（非 ORM）

**替代方案**: 純 pymysql、SQLAlchemy ORM

**理由**:
- EAV 批量插入用 Core 的 bulk insert 效率高
- 不需要 ORM 的 identity map / session 管理
- 比純 pymysql 更安全（參數綁定）且更易維護

### 6. 配置管理：YAML config

**選擇**: YAML 配置檔管理監聽路徑、MySQL 連線、解析規則

**理由**:
- 監聽路徑尚未確定，需要可配置
- MySQL 連線資訊不應寫死
- 未來擴展多機型時只需新增配置

## Risks / Trade-offs

- **網路路徑穩定性** → 網路斷線時 watchdog 可能錯過事件。Mitigation: 加入定時全量掃描作為補償機制，對比已入庫記錄與磁碟檔案的 mtime。
- **大檔案解析效能** → PRM 檔約 300KB，含數百參數。Mitigation: 批量 insert，單次 commit，預估單檔解析 < 2 秒。
- **檔案寫入中途觸發** → EAP 寫入大檔案時 watchdog 可能提前觸發。Mitigation: debounce 等待檔案 mtime 穩定後再解析。
- **重複解析** → 同一檔案被覆蓋多次。Mitigation: 每次解析都寫入新記錄（帶時間戳），不做 upsert，保留歷史。
- **SQLite RPM 檔案鎖** → 如果 EAP 正在寫入 RPM。Mitigation: 解壓到暫存目錄後再讀取 SQLite，避免直接存取原始檔案。

## Open Questions

- LOT ID 對接方式：從 MES API 查詢？還是從 EAP 其他檔案取得？
- 是否需要支援 KS 以外的其他機型（如 ASM）？
- 定時全量掃描的頻率？
- 服務部署形態：作為 Windows Service 還是排程任務？
