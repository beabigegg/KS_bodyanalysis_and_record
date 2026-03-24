## Context

比較頁面（cross-machine compare）的 Parameter Diff 區塊目前以 flat list 回傳所有 `recipe_params` rows，前端僅能依 `file_type` + `param_name` 排序呈現。一份 recipe 可能包含 300–600 個參數，工程師需要手動在清單中找出目標製程階段（如 bond1）的參數，效率低。

`param_name` 的結構為 `{role}/{pp_body}`（例：`parms/B1_Force_Seg_01`），其中 PP body 的前綴（`B1_`、`EFO_` 等）具有明確的製程語意，可靜態映射至 stage（製程階段）和 category（功能域）。

## Goals / Non-Goals

**Goals:**
- 定義靜態映射表，將 `param_name` 解析為 `(stage, category)`
- Compare API 在 param rows 中附加 `stage`、`category` 欄位
- 前端 Parameter Diff 改為 stage → category 折疊分組
- 未知前綴自動歸入 `_unmapped/{prefix}`，不丟失任何資料

**Non-Goals:**
- 不修改 `recipe_params` 資料庫欄位（分類為計算欄位，不持久化）
- 不支援使用者自訂分類規則（第一版）
- 不修改非比較頁面的參數顯示邏輯

## Decisions

### D1：分類邏輯置於後端（Backend Enrichment）

**選擇**：在 `compare.py` 呼叫 `ParamClassifier` 填入 `stage`/`category`，作為 API response 的計算欄位。

**理由**：
- 分類邏輯集中在 Python，可單元測試
- 若未來其他功能（搜尋、過濾、趨勢分析）需要分類，邏輯不重複
- 相對於前端 TypeScript lookup，Python dict 較易維護大型映射表

**捨棄方案**：前端 TypeScript mapping table — 若後續 API 需要依 stage 過濾，前端分類無法滿足需求。

### D2：映射表結構 — 靜態 Python module

```python
# param_classifier.py

# PRM PP body prefix → (stage, category | None)
# category=None 表示需進一步解析（如 seg_NN）
PP_PREFIX_MAP: dict[str, tuple[str, str | None]] = {
    "EFO": ("ball_formation", "efo"),
    "FAB": ("ball_formation", "fab"),
    "SBD": ("ball_formation", "detection"),
    "LBD": ("ball_formation", "detection"),
    "B1":  ("bond1", None),
    "BD1": ("bond1", None),
    "Equ": ("_unmapped", "equalization"),   # 第一版 fallback
    "LK":  ("loop", "profile"),
    "LP":  ("loop", "profile"),
    "J":   ("loop", "other"),
    "Span":("loop", "shaping"),
    "Flat":("loop", "shaping"),
    "Bal": ("loop", "balance"),
    "B2":  ("bond2", None),
    "BD2": ("bond2", None),
    "Tail":("bond2", "tail"),
    "SSB": ("bond2", "ssb"),
    "QS":  ("quick_adjust", "stitch"),
    "QK":  ("quick_adjust", "bond"),
    "QB":  ("quick_adjust", "bond"),
    "NSOP":("quality", "nsop"),
    "NSOL":("quality", "nsol"),
    "SHTL":("quality", "shtl"),
    "BITS":("quality", "general"),
}

# PHY role → keyword → category
MAG_HANDLER_KEYWORD_MAP = { "SLOT": "slot", "PITCH": "slot", ... }
WORKHOLDER_KEYWORD_MAP  = { "CLAMP": "clamp", "INDEX": "indexing", ... }

# REF role → keyword → category
DIE_REF_KEYWORD_MAP  = { "num_sites": "geometry", "eyepoint": "eyepoint", ... }
LEAD_REF_KEYWORD_MAP = { ..., "corridor": "vll", ... }
```

**理由**：單一 Python file，import 成本極低，不需要 DB 或 YAML config。

### D3：seg_NN 動態提取

`B1_`/`B2_`/`BD1_`/`BD2_` 的 category 從 pp_body 中用 regex 提取：

```python
import re
_SEG_RE = re.compile(r'_Seg_(\d+)', re.IGNORECASE)

def _seg_category(pp_body: str) -> str:
    m = _SEG_RE.search(pp_body)
    return f"seg_{m.group(1).zfill(2)}" if m else "misc"
```

**理由**：bond 段數因 recipe 不同而異（2–8 段），靜態枚舉 seg_01..seg_08 過於冗長且易漏；regex 一次解決。

### D4：PHY/REF 關鍵字匹配策略

PHY 和 REF 的 pp_body 無統一的底線前綴慣例（如 `IN_FIRST_SLOT`、`eyepoint_x_1`），改用 **substring 匹配**（大寫化後 `in` 查找）：

```python
def _keyword_category(body_upper: str, keyword_map: dict[str, str]) -> str:
    for keyword, cat in keyword_map.items():
        if keyword in body_upper:
            return cat
    return "other"
```

**理由**：keyword list 可獨立擴充，不需要完整枚舉所有參數名。有多個 keyword 匹配時，dict 的定義順序決定優先順序（Python 3.7+ 保證），可控。

### D5：LF/MAG flat，HB 三溫區

- `LF`、`MAG`：stage=None, category=None（前端直接 flat 顯示）
- `HB`：keyword 匹配 → `bond_site` / `preheat` / `post_heat`

**理由**：LF/MAG 參數量少（5–8 個），分組無附加價值；HB 有明確溫區語意值得分組。

## Risks / Trade-offs

- **映射表不完整** → 未知前綴落入 `_unmapped`，不丟失資料，定期 review 補齊
- **PHY/REF keyword 衝突**（同一 param_name 含多個 keyword）→ 以 dict 順序取第一個，設計時優先列更具體的 keyword
- **API response 增大** → stage/category 為短字串，對 300–600 row 的 response 影響可忽略
- **前端需重構 DiffTable** → 分組 accordion 是新的 UI pattern，需額外開發；設計為可選 prop（`groupBy?: boolean`），不影響其他用到 DiffTable 的地方

## Open Questions

- `Equ_` 的完整參數名稱清單待從真實 PP body 累積後補入 dispatch 表（目前全部 `_unmapped/equalization`）
- `J_` 的確切語意（BGA Jump 或其他）待確認後歸位至正確 stage/category
