## Context

目前 PRM 參數分類透過 `web/utils/param_classifier.py` 的硬編碼 keyword mapping 和 `web/config/prm_semantics.json` 的 regex 規則，在查詢時動態計算 stage/category。分類結果不落地到資料庫，而是在 API 回傳時即時附加。

使用者（製程工程師）反映目前的技術分類（stage/category）不夠直觀，他們更習慣按 wire bonding 製程流程來理解參數。新的 `K&S_Recipe_Organized_by_Process.csv`（~1995 筆）提供了 `process_step_logic` 欄位，將每個 PRM 參數映射到 7 個製程步驟。

## Goals / Non-Goals

**Goals:**
- 將 CSV 的 `process_step_logic` 映射整合進分類器，輸出新的 `process_step` 語意欄位
- 利用 CSV 中修正過的 stage/category 值來改善現有分類品質（減少 `_unmapped`）
- 前端參數瀏覽器新增 `process_step` facet 和欄位顯示
- 比對功能同步支援 `process_step` 欄位
- CSV 匯出包含 `process_step`

**Non-Goals:**
- 不改變 DB schema — `process_step` 與改善後的分類一樣由分類器即時計算，不新增資料庫欄位
- 不變更非 PRM 檔案類型的分類邏輯
- 不重寫整個分類器架構 — 保持現有 keyword + semantics 兩層機制，新增 lookup 為第三層

## Decisions

### Decision 1: Lookup table 作為分類器第三層（優先於 keyword mapping）

**選擇**: 將 CSV 轉為 JSON lookup dict（key = `param_name`），在分類器中作為最高優先級查詢層。若 lookup 命中則直接回傳完整語意（含 `process_step`），未命中則 fallback 到現有 keyword + semantics 邏輯。

**替代方案**:
- A) 直接修改 keyword mapping 程式碼 → 維護困難，每次更新需改 code
- B) 全部改用 CSV 驅動 → 新參數若不在 CSV 中會完全無分類

**理由**: Lookup 優先 + fallback 保留既有覆蓋率，且 CSV 更新只需換檔案不改程式碼。

### Decision 2: CSV 轉換為 JSON 靜態檔案

**選擇**: 提供轉換腳本將 `K&S_Recipe_Organized_by_Process.csv` 轉為 `web/config/process_step_lookup.json`，格式為 `{ "param_name": { "process_step": "...", "stage": "...", "category": "...", ... } }`。分類器啟動時載入此 JSON。

**理由**: JSON 載入比 CSV parsing 快，結構化查詢方便，且與現有 `prm_semantics.json` 配置模式一致。

### Decision 3: process_step 作為 ParamSemantics 新欄位

**選擇**: 在 `ParamSemantics` dataclass 新增 `process_step: str | None` 欄位。前端 API 回傳時自動包含。

**替代方案**: 獨立 API 端點提供 process_step mapping → 增加前端複雜度，需額外請求。

**理由**: 與現有 stage/category/family/feature 欄位一致的擴充模式，前端無需額外 API 呼叫。

### Decision 4: Lookup 同時修正 stage/category

**選擇**: 當 lookup 命中時，CSV 中的 stage/category 值覆蓋 keyword mapping 結果。這讓 CSV 中修正過的分類（例如原本 `_unmapped` 的參數）生效。

**理由**: CSV 是人工校正過的參考資料，分類品質優於自動 keyword matching。

## Risks / Trade-offs

- **[CSV 覆蓋率]** CSV 僅含 ~1995 筆參數，新機台或新版本 recipe 可能有未收錄的參數 → 未命中時 fallback 到既有分類器，`process_step` 為 null
- **[CSV 維護]** 未來新參數需手動更新 CSV → 提供轉換腳本降低更新門檻，且 fallback 機制確保系統不中斷
- **[stage/category 覆蓋]** CSV 覆蓋可能改變已建立的分類慣例 → 限制覆蓋僅發生在 CSV 明確提供值的欄位，空值不覆蓋
