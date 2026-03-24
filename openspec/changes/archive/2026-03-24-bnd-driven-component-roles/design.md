## Context

KS ConnX Elite 的 Process Program 由一個 BND 主檔連結多個 component 檔案。每個 component 的機台角色（mag_handler、workholder、die_ref、lead_ref 等）記錄在 BND 的兩個區段：

1. **Top-level 宣告區**（關鍵字 → 檔名）：`mag_handler`、`workholder`、`lead_frame`、`magazine`、`heat_block`、`indexer_ref_system`、`parms`、`ref`
2. **`master_device` block**：`mdref N { ref X.REF }`（引用已宣告的 REF）與 `master_wire_chain 0 X.WIR`（WIR 連結）

目前 pipeline 未解析 BND 角色，直接以 `Path(file).stem` 作為 die 前綴，產生如 `CJ621A20/param_name` 的無語意代碼。REF 檔內部有 `ref_type` 欄位（`DIE` / `LEAD`），可補充 REF 的語意角色。

兩個 sample 的觀察：
- PJA3406：兩個 PRM（`CJ621A20.PRM` 含 BSG、`CJ621A41.PRM` 無 BSG，值完全相同）
- PJS6400：只有一個 PRM（`AP643419.PRM` 含 BSG）
- 每個 PP 有兩個 REF（一個 DIE ref、一個 LEAD ref），順序不固定

## Goals / Non-Goals

**Goals:**
- 新增 `BNDRegistryParser`，解析 BND 建立 `ComponentRegistry`（stem → role 映射）
- 在 pipeline 解析 component 時，以語意角色取代時間戳記 stem 作為 param_name 前綴
- BSG-aware 邏輯：多個 `parms` 時，有 BSG 差異或值差異才保留為 `parms_2`，否則合併為 `parms`
- REF 角色從 REF 檔內部的 `ref_type` 欄位讀取（`DIE` → `die_ref`，`LEAD` → `lead_ref`）

**Non-Goals:**
- 不解析 WIR 檔內容（只記錄其存在於 registry）
- 不解析 EYE / IEY 檔內容（附屬於 REF，不寫入 recipe_params）
- 不解析 REF 的 bond position 資料（只讀 ref_type 和 name 欄位）
- 不改變 BND machine-level 參數的解析方式（`mc_serial`、`wire_size` 等仍由現有邏輯處理）
- 不處理三個以上 PRM 的情境（目前 sample 最多兩個）

## Decisions

### Decision 1：BNDRegistryParser 獨立於現有 BND SectionedParser

**選擇**：新增 `parsers/bnd_registry.py`，專責解析 ComponentRegistry；現有 `SectionedParser` 繼續處理 BND 的 machine-level 參數。

**理由**：兩者目的不同——registry 解析是「建立角色映射」，machine-level 解析是「提取參數值」。合併會造成職責混亂。`pipeline.py` 在開始解析 component 前先呼叫 `BNDRegistryParser.parse(bnd_path)`。

### Decision 2：ComponentRegistry 以 dataclass 表示

```python
@dataclass
class ParmsEntry:
    stem: str
    has_bsg: bool

@dataclass
class RefEntry:
    stem: str
    ref_type: str    # "DIE" | "LEAD"，從 REF 檔內部讀取
    name: str        # 供 debug 用

@dataclass
class ComponentRegistry:
    mag_handler:   str
    workholder:    str
    lead_frame:    str
    magazine:      str
    heat_block:    str
    indexer_ref:   str
    wire_stem:     str           # master_wire_chain 的 stem
    parms_list:    list[ParmsEntry]
    ref_list:      list[RefEntry]
    machine_stem:  str
    product_stem:  str | None
```

**理由**：dataclass 明確且可測試；pipeline 直接使用欄位而非 dict，避免 KeyError。

### Decision 3：parms_2 的 BSG-aware 合併策略

```
若 len(parms_list) == 1：
    → 直接用 "parms" 前綴

若 len(parms_list) >= 2：
    p1, p2 = parms_list[0], parms_list[1]
    if p1.has_bsg != p2.has_bsg → 保留兩個（BSG 結構差異）
    elif p1.param_values != p2.param_values → 保留兩個（值差異）
    else → 只保留 p1（合併為 "parms"，丟棄 p2）

命名：第一個 → "parms"，第二個 → "parms_2"
```

**理由**：即使 PRM 值相同，BSG 有無本身就是結構差異，不能靜默丟棄。值差異比較在 pipeline 層做（解析雙方 params 後比較），而非在 registry parser 層。

### Decision 4：REF ref_type 從 REF 檔內部讀取，而非從 BND 推斷

**選擇**：解析 REF 檔時讀取 `ref_type = DIE/LEAD` 欄位。

**理由**：BND 中 `ref` 關鍵字和 `mdref` 都沒有標示 DIE/LEAD 類型，但 REF 檔內部有明確的 `ref_type` 欄位。直接讀取比推斷可靠，且不依賴順序假設。

**實作方式**：`BNDRegistryParser` 在掃描 BND `ref X.REF` 行後，立即開啟對應的 REF 檔讀取前 20 行，提取 `ref_type` 和 `name` 欄位。

### Decision 5：唯一 component 不加前綴

LF、MAG、HB、IRS 每個 PP 只有一個，param_name 不加前綴，保持向後相容。
WIR 不寫入 recipe_params（純連結定義，無可比較參數值）。

## Risks / Trade-offs

**[BREAKING 資料格式]** PHY/PRM/REF 的 param_name 前綴格式全面改變
→ 緩解：與 fix-compare-and-extraction-gaps 同樣的 migration 策略——清空後重新 import。

**[BND 解析失敗]** 若 BND 格式異常或缺少必要關鍵字，registry 建立失敗
→ 緩解：`BNDRegistryParser` 採用寬鬆解析（missing field → None），pipeline 遇到 None role 時 fallback 到 `Path(file).stem` 前綴並記錄 warning。

**[REF 檔讀取開銷]** Registry parser 需額外打開每個 REF 檔讀取 ref_type
→ 緩解：REF 檔很小（< 5KB），只讀前 20 行，開銷可忽略。

**[三個以上 parms]** 若未來有 recipe 包含三個 PRM，目前邏輯只處理前兩個
→ 緩解：logging warning，第三個以上用 `parms_N` 命名，不中斷 import。

## Migration Plan

1. 部署新版 pipeline（含 BNDRegistryParser + 語意前綴）
2. 清空 `ksbody_recipe_params`、`ksbody_recipe_import`（及所有 FK 關聯表）
3. 重新 import 所有現有 recipe body 檔案
4. 執行驗證：確認 `mag_handler/IN_FIRST_SLOT`、`die_ref/num_sites` 等格式出現在 DB

**Rollback**：回退 pipeline 版本後重新 import 即可。

## Open Questions

- BND 中是否可能有超過兩組 `ref`（即三個 die 或多層 stacked die）？目前只見過兩個。
- `master_device` 是否可能有多個（multi-site）？目前兩個 sample 都只有一個 `master_device 1`。
- `parms` 與 `mdref` 是否存在顯式對應關係（例如 BND 中 parms[0] 專屬於 mdref[1]）？目前判斷是 stem 隱式對應，尚未從手冊確認。
