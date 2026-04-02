## Why

Non-PRM file types（AIC, BND, HB, LF, LHM, MAG, PPC, VHM, WIR, PHY, REF）的分類欄位在前端顯示中沒有實際用途，佔據表格空間卻不提供有意義的資訊。需要根據 file type 隱藏這些無用欄位，讓使用者專注於有意義的數據。

## What Changes

- 在 VIEW 模式下，根據 file type 隱藏無用的分類欄位：
  - **AIC, BND, HB, LF, LHM, MAG, PPC, VHM, WIR**：隱藏 `param_group`, `stage`, `category`, `family`, `feature`, `instance`, `tunable`, `description`
  - **PHY, REF**：隱藏 `stage`, `category`, `family`, `feature`, `instance`, `tunable`, `description`（保留 `param_group`）
- 在 COMPARE 模式下套用相同的欄位隱藏邏輯
- PRM 維持現有行為，所有分類欄位繼續顯示

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `param-browser`: VIEW 和 COMPARE 模式下根據 file type 條件隱藏分類欄位

## Impact

- 前端 `ImportDetailPage.tsx`：`toParamTableRows()` 需根據 file_type 排除欄位
- 前端 `ObjectTable.tsx`：可能需要支援欄位過濾或由上層傳入已過濾的資料
- 前端 `DiffTable.tsx`：`HIDDEN_KEYS` 需依 file type 動態調整
- 前端 `GroupedDiffTable.tsx`：分組邏輯可能需配合調整
