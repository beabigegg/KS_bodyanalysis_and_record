## Context

現有 PRM process-step mapping 主要來自 `web/config/process_step_lookup.json`，其內容由 `scripts/build_process_step_lookup.py` 從 `K&S_Recipe_Organized_by_Process.csv` 轉出，再由 `web/utils/param_classifier.py` 在分類時直接套用。實際資料中已有一批帶有明確 `Bond1`、`Bump`、`Bond2` 前綴的參數仍被標成 `7. 系統/監控/其他 (System & Monitoring)`，代表來源資料或轉換結果存在過度泛化的歸類。

這類錯置不是一般 keyword fallback 的問題，而是 lookup 本身把「具體製程參數」寫成「泛系統類」。只修 classifier 顯示層不夠，因為 JSON lookup 仍會持續把錯誤值帶進測試、瀏覽與後續資料更新流程。

## Goals / Non-Goals

**Goals:**
- 讓帶有 `Bond1`、`Bump`、`Bond2` 前綴的 PRM 參數在 lookup 中優先對應到各自的 bond-related process step。
- 將修正放在 lookup 建置或驗證流程，避免人工調整 JSON 後下次重建又被覆蓋。
- 補上回歸測試，覆蓋至少一個 `Bond1`、`Bump`、`Bond2` 前綴且原本容易被歸到 `System & Monitoring` 的案例。

**Non-Goals:**
- 不重做整份 CSV 的 process-step taxonomy。
- 不變更非 `Bond1`、`Bump`、`Bond2` 前綴參數的分類規則。
- 不重新設計 `stage`、`category`、`family`、`feature` 的語意模型。

## Decisions

### Decision 1: Use prefix-aware correction in lookup generation

選擇在 `build_process_step_lookup.py` 增加一層 prefix-aware correction，而不是只手改 `process_step_lookup.json`。若 `param_name` 的主體以前綴可明確判定屬於 `Bond1`、`Bump`、`Bond2`，且來源 `process_step` 仍是 `7. 系統/監控/其他 (System & Monitoring)`，腳本 SHALL 將它改寫為對應的 bond process step。

這樣可以讓規則跟著資料重建流程一起存在，避免 JSON 每次重生都回歸。

替代方案：
- 只手改 `process_step_lookup.json`。缺點是不可持續，下一次由 CSV 重建就會消失。
- 只在 `ParamClassifier` runtime 做覆寫。缺點是 source-of-truth 仍錯，測試與資料檢查不一致。

### Decision 2: Treat System & Monitoring as a fallback, not a default for bond-prefixed PRM

`System & Monitoring` 對 bond-prefixed PRM 只能作為沒有更具體製程步驟可推定時的保底值。對 `Bond1*` 與 `Bump*`，修正目標是 `2. BOND1 相關 / BUMP (First Bond)`；對 `Bond2*`，修正目標是 `6. BOND2 相關 (Second Bond / Tail)`。

這個規則只在來源值是 `System & Monitoring` 時生效，不會覆蓋已經是 `Looping` 或其他更具體步驟的資料，以免把少數特殊參數誤拉回 bond step。

### Decision 3: Verify corrected behavior at both build and classification boundaries

除了檢查轉換腳本輸出，還要驗證 `ParamClassifier` 對 lookup-covered 參數實際回傳的 `process_step` 已是修正後值。這可確保修改不只停留在資料檔，也真的影響使用者可見結果。

## Risks / Trade-offs

- **[Prefix heuristic overreach]** 若某些 `Bond1` 或 `Bond2` 前綴參數其實刻意屬於系統設定，prefix correction 可能會把少數例外拉回製程步驟。
  Mitigation: 只在來源值為 `System & Monitoring` 時修正，並用已知錯例建立測試，必要時加入明確例外清單。

- **[Source CSV inconsistency remains]** 原始 CSV 仍可能保留舊分類，造成規則依賴建置腳本而非原始資料本身。
  Mitigation: 將修正規則集中在建置腳本並記錄原因，後續若 CSV 更新可再把規則移除或縮小。

- **[Partial coverage]** 這次只處理 `Bond1`、`Bump`、`Bond2` 前綴，其他可能錯置的 prefix 仍會留待之後處理。
  Mitigation: 將規則寫成可擴充的 prefix-to-process-step 映射，後續補新 prefix 時不需重構。
