## Why

Recipe Import Records 頁面目前僅提供查詢功能，缺乏資料維護能力。當匯入了錯誤或不再需要的 recipe 記錄時，使用者無法從介面上移除，只能直接操作資料庫。需要提供刪除功能以支援日常資料維護。

## What Changes

- 新增單筆刪除：在每筆 import record 的列表行上提供刪除按鈕，點擊後確認刪除
- 新增多筆刪除：提供 checkbox 勾選機制，可一次選取多筆記錄批次刪除
- 後端新增 DELETE API endpoints（單筆 + 批次），刪除 import record 時連帶清除所有關聯子表資料（params、app_spec、bsg、rpm_limits、rpm_reference、wir_group_map）
- 前端刪除後自動刷新列表

## Capabilities

### New Capabilities
- `recipe-import-delete`: Recipe import record 的刪除功能，包含單筆刪除與批次刪除的 API 及前端互動

### Modified Capabilities
- `webui-backend`: 新增 DELETE endpoints 至 imports router

## Impact

- **Backend**: `web/routes/imports.py` — 新增 DELETE `/{import_id}` 和 DELETE `/batch` endpoints
- **Frontend**: `web/frontend/src/pages/ImportListPage.tsx` — 新增 checkbox 選取、刪除按鈕、確認對話框
- **Database**: 刪除操作涉及 `recipe_import` 及所有以 `recipe_import_id` 為 FK 的子表（recipe_params, recipe_app_spec, recipe_bsg, recipe_rpm_limits, recipe_rpm_reference, recipe_wir_group_map）
- **No breaking changes**: 純新增功能，不影響現有查詢或匯入流程
