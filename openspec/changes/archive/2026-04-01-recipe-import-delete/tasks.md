## 1. Backend — Delete API endpoints

- [x] 1.1 Add writable DB connection dependency (`get_writable_connection` or use `engine.begin()`) in `deps.py` for delete operations
- [x] 1.2 Implement `DELETE /api/imports/{import_id}` endpoint in `web/routes/imports.py` — delete child tables (recipe_params, recipe_app_spec, recipe_bsg, recipe_rpm_limits, recipe_rpm_reference, recipe_wir_group_map) then delete import record, all in one transaction. Return 404 if not found.
- [x] 1.3 Implement `DELETE /api/imports/batch` endpoint in `web/routes/imports.py` — accept `{"ids": [...]}` body, validate non-empty, delete all matching records and children in one transaction, return deleted count. Return 400 if ids list is empty.

## 2. Frontend — Selection UI

- [x] 2.1 Add `selected` state (Set<number>) to `ImportListPage.tsx`
- [x] 2.2 Add header checkbox (select all / deselect all on current page) and per-row checkbox in the table
- [x] 2.3 Clear selection when `page` or `filters` change

## 3. Frontend — Delete actions

- [x] 3.1 Add single-row delete button in the action column, with `window.confirm()` confirmation and API call (`api.delete`)
- [x] 3.2 Add batch delete button (shown when selection is non-empty, displaying selected count), with `window.confirm()` and batch API call
- [x] 3.3 After successful delete (single or batch), clear selection and refresh the list by re-triggering the data fetch

## 4. Testing

- [x] 4.1 Add backend tests for single delete endpoint (success + 404 case)
- [x] 4.2 Add backend tests for batch delete endpoint (success + empty list 400 + partial invalid IDs)
