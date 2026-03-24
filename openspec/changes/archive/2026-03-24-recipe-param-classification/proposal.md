## Why

比較頁面目前以 flat list 呈現數百個 `param_name`，工程師調機時需要手動在 `B1_`、`B2_` 等前綴中逐行尋找相關參數。引入 stage × category 分組後，工程師可直接展開目標製程階段（如 `bond1`）查看所有差異，大幅縮短比較定位時間。

## What Changes

- 新增 `ParamClassifier` 模組，根據 `param_name`（role prefix + PP body）靜態映射至 `(stage, category)`
- Compare API 回傳的每筆 param row 增加 `stage` 和 `category` 欄位
- 前端比較頁面 Parameter Diff 區塊改為 stage → category 折疊分組顯示
- 未知前綴自動歸入 `_unmapped/{prefix}`，供後續補齊映射表

## Capabilities

### New Capabilities

- `recipe-param-classification`: 定義 param_name 的 stage/category 分類規則（PRM stage 映射、PHY/REF 關鍵字分組、LF/MAG/HB flat 策略、_unmapped fallback）

### Modified Capabilities

- `cross-machine-compare`: Compare API 回傳的 param rows 新增 `stage` 和 `category` 欄位；前端改為分組摺疊顯示

## Impact

- `web/routes/compare.py`：enrich param_diff rows with stage/category
- 新增 `param_classifier.py`（或 `web/utils/param_classifier.py`）
- `web/frontend/src/pages/ComparePage.tsx`：grouped accordion UI
- `web/frontend/src/components/DiffTable.tsx`：可能需要新增分組 variant 或新 component
- `web/frontend/src/types.ts`：CompareRow type 增加 stage/category 欄位
- 新增測試 `tests/test_param_classifier.py`
