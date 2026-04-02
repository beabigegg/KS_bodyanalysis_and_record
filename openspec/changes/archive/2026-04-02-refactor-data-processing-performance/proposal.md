## Why

目前 PRM 參數分類使用程式碼內建的 keyword mapping（`param_classifier.py`）和 regex 語意字典（`prm_semantics.json`），產出 `stage` / `category` 等技術分類欄位。但對使用者（製程工程師）來說，他們習慣以 **wire bonding 製程流程順序** 來理解參數——從燒球 → Bond1 → Neck → Loop → 2nd Approach → Bond2 → 系統監控。現有分類缺少這個製程流程維度，導致瀏覽和篩選不直觀。

新增的 `K&S_Recipe_Organized_by_Process.csv` 提供了 ~1995 筆參數的製程步驟映射（`process_step_logic`），同時也修正了部分現有分類的 stage/category 值，並為 134 個 `_unmapped` 參數補上了正確的製程歸屬。

## What Changes

- 新增 `process_step` 欄位：將 CSV 中的 `process_step_logic` 作為 lookup table，為每個 PRM 參數標註所屬製程步驟
- 擴充分類器：利用 CSV 映射修正/補充現有 `param_classifier` 的 stage/category 分類結果，減少 `_unmapped` 數量
- UI 新增製程步驟篩選：在參數瀏覽頁面新增 `process_step` facet，讓使用者可依製程流程順序瀏覽參數
- 匯出 CSV 包含新欄位：導出時一併輸出 `process_step` 欄位

## Capabilities

### New Capabilities
- `process-step-mapping`: 基於 lookup CSV 將 PRM 參數映射到製程步驟（process_step_logic），提供製程流程維度的分類

### Modified Capabilities
- `recipe-param-classification`: 擴充分類器以整合 process-step lookup，修正 _unmapped 參數的 stage/category，並輸出新的 process_step 欄位
- `param-browser`: UI 新增 process_step facet 篩選與欄位顯示，支援依製程流程順序瀏覽

## Impact

- **程式碼**：`param_classifier.py` 需載入 lookup table 並擴充回傳欄位；前端參數瀏覽頁面需新增 facet 與欄位
- **資料庫**：`recipe_params` 表可能需新增 `process_step` 欄位，或在查詢時動態 join lookup
- **依賴**：新增 CSV lookup 檔案作為靜態參考資料，需隨專案版控
- **相容性**：既有 stage/category 值可能因修正而變動，compare 功能需同步更新
