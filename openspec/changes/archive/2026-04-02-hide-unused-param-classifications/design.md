## Context

PARAMS 的 VIEW 模式（ImportDetailPage）會透過 `toParamTableRows()` 為所有 file type 的行加入全部分類欄位（param_group, stage, category, family, feature, instance, tunable, description），再由 ObjectTable 自動顯示所有 key 為欄位。非 PRM file type 的分類欄位大多為空值，浪費表格空間。

COMPARE 模式（GroupedDiffTable → DiffTable）已經將 param_group、stage、category 隱藏不作為欄位顯示（改為階層分組），但 family、feature、instance、tunable、description 若出現仍會顯示。

## Goals / Non-Goals

**Goals:**
- VIEW 模式根據 file type 排除無用分類欄位，讓表格更精簡
- COMPARE 模式套用相同的隱藏邏輯
- PRM 保持現有完整分類欄位不受影響

**Non-Goals:**
- 不變更後端 API 回傳的資料結構（前端過濾即可）
- 不變更分類器邏輯
- 不影響 GroupedDiffTable 的階層分組邏輯（PRM 仍按 param_group → stage → category 分組）

## Decisions

### Decision 1: 前端過濾，不改後端

在 `toParamTableRows()` 中根據 `file_type` 決定要包含哪些欄位。ObjectTable 是 key-driven，只要 row 物件不包含某 key，欄位就不會出現。

**替代方案：** 後端不回傳這些欄位 — 拒絕，因為後端資料可能有其他用途（匯出 CSV 等），且修改後端 API 的影響範圍更大。

### Decision 2: 定義欄位隱藏映射表

建立一個 `HIDDEN_CLASSIFICATION_KEYS` 映射，定義每種 file type 要隱藏的欄位清單：

```typescript
const CLASSIFICATION_KEYS = ['param_group', 'stage', 'category', 'family', 'feature', 'instance', 'tunable', 'description']

// 只有 PRM 需要全部分類欄位
// PHY, REF 保留 param_group
// 其餘 file type 全部隱藏
function getHiddenClassificationKeys(fileType: string): Set<string> {
  if (fileType === 'PRM') return new Set()
  if (fileType === 'PHY' || fileType === 'REF') {
    return new Set(CLASSIFICATION_KEYS.filter(k => k !== 'param_group'))
  }
  return new Set(CLASSIFICATION_KEYS)
}
```

### Decision 3: COMPARE 模式 — 擴展 DiffTable 的 HIDDEN_KEYS

DiffTable 目前靜態定義 `HIDDEN_KEYS`。改為根據當前顯示的 rows 的 file_type 決定額外要隱藏的分類欄位。由於 COMPARE 可能混合多種 file_type，策略為：只有當 **所有行** 的某欄位都是空值時才隱藏該欄位。

**替代方案：** 由 GroupedDiffTable 在傳遞 rows 時先刪除空欄位 — 也可行，但在 DiffTable 統一處理更簡潔。

## Risks / Trade-offs

- [風險] VIEW 模式若同時顯示多個 file type 的 rows，不同 file type 的行有不同欄位數 → ObjectTable 會以所有 rows 的 key 聯集為 headers，部分行的欄位為空白。
  → 緩解：目前 VIEW 模式已按 file_type 分開顯示，不會混合，所以不成問題。
- [風險] COMPARE 模式混合 file type 時，某些行有 family/feature 而其他沒有
  → 緩解：採用「全空則隱藏」策略，若 PRM 行存在則欄位仍會顯示。
