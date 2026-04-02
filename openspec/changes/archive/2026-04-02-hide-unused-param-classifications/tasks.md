## 1. 建立欄位隱藏工具函式

- [x] 1.1 在前端建立 `getHiddenClassificationKeys(fileType: string): Set<string>` 工具函式，定義各 file type 的隱藏欄位映射（PRM 不隱藏、PHY/REF 保留 param_group、其餘全隱藏）

## 2. VIEW 模式 — ImportDetailPage

- [x] 2.1 修改 `toParamTableRows()` 函式，根據 row 的 `file_type` 呼叫隱藏映射，從輸出物件中排除對應的分類欄位 key

## 3. COMPARE 模式 — DiffTable

- [x] 3.1 修改 `DiffTable` 元件，在計算 `metaKeys` 時，除了靜態 `HIDDEN_KEYS` 之外，再過濾掉所有 rows 中值皆為空（null / undefined / 空字串）的分類欄位
