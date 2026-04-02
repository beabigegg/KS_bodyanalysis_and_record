## 1. Backend compare selection API

- [x] 1.1 Add compare parameter catalog request and response models plus shared semantic row helpers for multi-import parameter browsing.
- [x] 1.2 Implement `POST /api/compare/params/catalog` with selected-import validation, file-type and semantic filters, facet counts, and paged parameter rows.
- [x] 1.3 Extend `POST /api/compare` so the `params` section can be scoped by selected `(file_type, param_name)` keys without regressing APP, BSG, or RPM sections.
- [x] 1.4 Add route-level tests for catalog facets, partially present parameters, and scoped parameter compare output.

## 2. Frontend two-step compare workflow

- [x] 2.1 Refactor `web/frontend/src/pages/ComparePage.tsx` into import selection, parameter selection, and compare results phases.
- [x] 2.2 Build the compare parameter-selection UI with file type overview, classification-aware filters, selectable parameter rows, and visible selected-count feedback.
- [x] 2.3 Update compare frontend types and API payloads to send selected parameter keys and to clear stale selections whenever the import set changes.

## 3. Shared compare browsing polish

- [x] 3.1 Reuse or extract shared classification visibility and labeling helpers so compare selection follows the same file-type-aware browsing rules as Recipe Import Records.
- [x] 3.2 Verify that APP, BSG, RPM Limits, and RPM Reference sections still work after the new selection gate and capture the coverage in tests or verification notes.
