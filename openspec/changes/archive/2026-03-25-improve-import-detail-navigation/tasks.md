## 1. Backend import-detail APIs

- [x] 1.1 Add shared helpers in `web/routes/imports.py` to derive `param_group`, `stage`, and `category` from stored parameter rows
- [x] 1.2 Implement `GET /api/imports/{id}/summary`
- [x] 1.3 Implement `GET /api/imports/{id}/param-facets`
- [x] 1.4 Replace the eager grouped `/api/imports/{id}/params` response with paged, filtered rows plus totals
- [x] 1.5 Keep APP/BSG/RPM endpoints unchanged except for lazy-load compatibility

## 2. Frontend import-detail flow

- [x] 2.1 Update import-detail API types and client helpers for summary, facets, and paged params
- [x] 2.2 Refactor `ImportDetailPage` to fetch summary/facets first and load tab data lazily
- [x] 2.3 Replace the flat file-type table flow with guided filters and paged parameter browsing
- [x] 2.4 Show section overview counts so users can see import scope before drilling into rows

## 3. Verification

- [x] 3.1 Add backend tests for summary, facets, and paged parameter responses
- [x] 3.2 Run targeted tests for imports route changes and existing parser/classifier coverage
