## 1. CSV-to-JSON 轉換腳本

- [x] 1.1 建立轉換腳本 `scripts/build_process_step_lookup.py`，讀取 `K&S_Recipe_Organized_by_Process.csv`，產出 `web/config/process_step_lookup.json`（key=param_name, value={process_step, stage, category, family, feature, description, tunable}）
- [x] 1.2 處理重複 param_name：保留首次出現，log warning
- [x] 1.3 執行腳本產生 `process_step_lookup.json` 並加入版控

## 2. 擴充 ParamSemantics 與分類器

- [x] 2.1 在 `web/utils/param_classifier.py` 的 `ParamSemantics` dataclass 新增 `process_step: str | None = None` 欄位
- [x] 2.2 新增 lookup loader：在 `ParamClassifier` 中載入 `process_step_lookup.json` 為 class-level dict（啟動時載入，缺檔時 fallback 空 dict）
- [x] 2.3 修改 `classify_semantics()` 方法：查詢 lookup dict 優先，命中時以非空欄位覆蓋 keyword/semantics 結果，並填入 `process_step`
- [x] 2.4 確認 `classify()` 回傳值相容（仍回傳 stage, category tuple），不影響既有呼叫者

## 3. 前端參數瀏覽器

- [x] 3.1 API 端點回傳 `process_step` 欄位：修改參數查詢 route 的 classification enrichment，加入 `process_step`
- [x] 3.2 PRM 參數表格新增 `process_step` 欄位（置於 param_group 之前）
- [x] 3.3 非 PRM 檔案類型隱藏 `process_step` 欄位
- [x] 3.4 新增 `process_step` facet 篩選器，選項依步驟編號排序（0→7）
- [x] 3.5 facet 計數隨篩選條件動態更新

## 4. 比對功能同步

- [x] 4.1 修改 `web/routes/compare.py` 的 classification enrichment，加入 `process_step`
- [x] 4.2 比對表格中若所有行的 `process_step` 為空則隱藏該欄位

## 5. CSV 匯出

- [x] 5.1 修改匯出邏輯，PRM 參數匯出時包含 `process_step` 欄位

## 6. 驗證

- [x] 6.1 確認 lookup 命中時 `_unmapped` 參數數量顯著減少
- [x] 6.2 確認 lookup 未命中時 fallback 行為正確（process_step=None，stage/category 不變）
- [x] 6.3 確認前端 process_step facet 篩選功能正常運作
