## 1. ParamClassifier 核心模組

- [x] 1.1 建立 `param_classifier.py`，定義 `PP_PREFIX_MAP` 靜態映射表（EFO/FAB/SBD/LBD/B1/BD1/LK/LP/J/Span/Flat/Bal/B2/BD2/Tail/SSB/QS/QK/QB/NSOP/NSOL/SHTL/BITS/Equ）
- [x] 1.2 實作 `_seg_category(pp_body)` — regex 提取 `_Seg_NN` → `"seg_01"` 等，無則回傳 `"misc"`
- [x] 1.3 定義 `MAG_HANDLER_KEYWORD_MAP` 和 `WORKHOLDER_KEYWORD_MAP`，實作 `_keyword_category()` substring 匹配
- [x] 1.4 定義 `DIE_REF_KEYWORD_MAP` 和 `LEAD_REF_KEYWORD_MAP`（含 `corridor` → `vll`）
- [x] 1.5 定義 `HB_KEYWORD_MAP`（bond_site / preheat / post_heat）
- [x] 1.6 實作 `classify(param_name: str, file_type: str) -> tuple[str | None, str | None]` 主函式，依 role 分支呼叫對應策略；LF/MAG 回傳 `(None, None)`；未知 prefix 回傳 `("_unmapped", prefix_lower)`

## 2. 後端 Compare API 擴充

- [x] 2.1 在 `web/routes/compare.py` 的 `_diff_rows()` 回傳結果中，對每筆 row 呼叫 `ParamClassifier.classify()` 附加 `stage` 和 `category`
- [x] 2.2 確認 `stage` 和 `category` 為 `str | None`，`None` 值序列化為 JSON `null`

## 3. 前端型別更新

- [x] 3.1 在 `web/frontend/src/types.ts` 的 `CompareRow` type 新增 `stage: string | null` 和 `category: string | null`

## 4. 前端分組 UI

- [x] 4.1 建立 `web/frontend/src/components/GroupedDiffTable.tsx`，接受 `rows: CompareRow[]`，依 `stage → category` 兩層折疊呈現
- [x] 4.2 `GroupedDiffTable` — stage 群組標頭顯示 diff 數量，預設展開有 diff 的群組
- [x] 4.3 `GroupedDiffTable` — `stage = null` 的 row 不分組（flat），`stage = "_unmapped"` 歸入「未分類」區塊
- [x] 4.4 在 `ComparePage.tsx` 將 Parameter Diff 的 `<DiffTable>` 替換為 `<GroupedDiffTable>`

## 5. 測試

- [x] 5.1 建立 `tests/test_param_classifier.py`，覆蓋以下場景：
  - B1_Force_Seg_01 → (bond1, seg_01)
  - B1_Contact_Level → (bond1, misc)
  - EFO_Power → (ball_formation, efo)
  - Bal_Loop_Percent → (loop, balance)
  - mag_handler/IN_FIRST_SLOT → (None, slot)
  - workholder/LOT_SEP_MODES → (None, indexing)
  - die_ref/eyepoint_x_1 → (None, eyepoint)
  - lead_ref/corridor_length → (None, vll)
  - LF file_type → (None, None)
  - Unknown prefix XYZ_ → (_unmapped, xyz)
  - Equ_Factor → (_unmapped, equalization)

