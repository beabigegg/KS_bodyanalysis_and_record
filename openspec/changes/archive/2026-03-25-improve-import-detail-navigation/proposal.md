## Why

Recipe import detail currently loads every parameter dataset up front and renders it as generic wide tables. A single KS recipe import can contain thousands of parameter rows, so users enter the detail page without a clear summary and must sift through a large payload before they can orient themselves.

## What Changes

- Add import-detail summary data so the UI can show dataset size and available sections before loading full detail rows.
- Add server-side parameter browsing endpoints that return facets and paged parameter rows instead of forcing the client to fetch all parameters at once.
- Update the import detail page to load summary first, fetch tab data lazily, and guide users through file type and parameter-group navigation.
- Exclude duplicated raw BSG parameter browsing from the default parameter view when a dedicated BSG detail view already exists.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `param-browser`: Import detail browsing changes from eager full-detail loading to summary-first, filterable, paged parameter exploration.
- `webui-backend`: Import detail APIs add summary and paged/faceted parameter endpoints for incremental loading.

## Impact

- Backend: [web/routes/imports.py](D:/WORK/user_scrip/TOOL/KS_bodyanalysis_and_record/web/routes/imports.py) will gain new summary/facets/paged param responses.
- Frontend: [web/frontend/src/pages/ImportDetailPage.tsx](D:/WORK/user_scrip/TOOL/KS_bodyanalysis_and_record/web/frontend/src/pages/ImportDetailPage.tsx) and supporting types/API helpers will be reworked around lazy loading.
- Tests: API coverage should be added for the new response shapes and import-detail browsing behavior.
