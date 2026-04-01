## Context

Recipe Import Records 頁面（`ImportListPage.tsx`）目前僅有查詢功能，後端 `web/routes/imports.py` 只提供 GET endpoints。使用者無法從 UI 刪除錯誤或不需要的匯入記錄。

資料庫結構：`recipe_import` 為主表，有 6 張子表透過 `recipe_import_id` FK 關聯（recipe_params, recipe_app_spec, recipe_bsg, recipe_rpm_limits, recipe_rpm_reference, recipe_wir_group_map）。

## Goals / Non-Goals

**Goals:**
- 支援單筆刪除：使用者可刪除指定的一筆 import record
- 支援批次刪除：使用者可勾選多筆記錄一次刪除
- 刪除時級聯清除所有關聯子表資料
- 刪除前要求使用者確認，防止誤刪

**Non-Goals:**
- 不提供軟刪除（soft delete）機制，直接物理刪除
- 不提供復原/回收站功能
- 不修改匯入流程或其他現有功能

## Decisions

### 1. 級聯刪除策略：應用層逐表刪除

在 Python 層依序刪除子表再刪主表，而非依賴資料庫 CASCADE。

**理由**: 現有 schema 定義中 FK 未設定 ON DELETE CASCADE，且避免修改 DB schema 帶來的遷移風險。應用層刪除也更容易控制順序和錯誤處理。

**替代方案**: 加 DB CASCADE — 需要 ALTER TABLE migration，對生產環境風險較高。

### 2. API 設計：兩個 DELETE endpoints

- `DELETE /api/imports/{import_id}` — 單筆刪除
- `DELETE /api/imports/batch` — 批次刪除，body 傳入 `{"ids": [1, 2, 3]}`

**理由**: 單筆刪除 RESTful 語義清晰；批次刪除避免前端發送大量個別請求。批次 endpoint 使用 POST-style body 傳 ID 列表，因為 DELETE with body 雖不標準但被主流框架支持，且語義更明確。

### 3. 前端交互：checkbox 選取 + 確認對話框

- 表頭新增全選 checkbox，每列新增勾選 checkbox
- 勾選後顯示批次刪除按鈕（含已選數量）
- 單筆刪除按鈕在每列操作欄
- 所有刪除操作使用 `window.confirm()` 確認

**理由**: `window.confirm()` 實作簡單且足夠防止誤操作，不需要自訂 modal。

### 4. 交易一致性

批次刪除在單一 DB transaction 中完成，確保全部成功或全部失敗。

## Risks / Trade-offs

- **[大量資料刪除可能較慢]** → 單筆 import 可能有上萬筆 params。批次刪除多筆時可能耗時較長。Mitigation: 前端顯示 loading 狀態，後端在 transaction 中逐表刪除。
- **[誤刪無法復原]** → 物理刪除後資料無法恢復。Mitigation: 刪除前強制 confirm 確認，批次刪除顯示即將刪除的數量。
- **[DELETE with body 非標準]** → 部分 proxy 可能 strip DELETE body。Mitigation: 如遇問題可改為 `POST /api/imports/batch-delete`，但目前 FastAPI 支援良好。
