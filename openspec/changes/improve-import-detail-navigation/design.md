## Context

The current import detail flow treats a KS recipe import as a single eager payload. The backend exposes `/api/imports/{id}/params` as a grouped full dump, and the frontend detail page immediately requests params, APP, BSG, and RPM together. This works for correctness but scales poorly for recipe imports with 5,000+ parameter rows and gives users no high-level orientation before they enter raw tables.

The parser and compare flows already contain useful semantic structure:
- parameter names are role-prefixed during pipeline import,
- compare responses enrich parameter rows with `param_group`, `stage`, `category`, and optional `wir_group_no`,
- BSG already has a dedicated normalized dataset.

The design goal is to reuse that structure in the import-detail browsing flow without changing parsing or storage semantics.

## Goals / Non-Goals

**Goals:**
- Add an import summary response that lets the UI show dataset size and available sections before loading detail rows.
- Add server-side parameter browsing with filters and pagination so the client can request only the slice being viewed.
- Expose parameter facets derived from stored parameter names and classifier output for guided navigation.
- Refactor the import detail page to load summary first and fetch tab data lazily.

**Non-Goals:**
- Rework compare, trend, or R2R flows in this change.
- Change parser output, database schema, or import pipeline semantics.
- Introduce virtualized tables or a complete visual redesign.

## Decisions

### 1. Keep existing storage model; build summary/facets on read

The database already stores normalized parameter rows in `ksbody_recipe_params`. This change will not add new tables or columns. Summary counts and browsing facets will be computed from existing rows at request time.

Alternative considered: persist pre-aggregated browsing metadata during import. Rejected because it would widen schema and pipeline scope for a UI problem that can be solved with indexed read queries.

### 2. Split parameter browsing into three API shapes

The import-detail API surface will be split into:
- `GET /api/imports/{id}/summary`
- `GET /api/imports/{id}/param-facets`
- `GET /api/imports/{id}/params`

`summary` returns top-level counts by section and file type.  
`param-facets` returns available file types, parameter groups, stages, and categories for the current import.  
`params` returns paged rows with server-side filters (`file_type`, `param_group`, `stage`, `category`, `search`, `page`, `page_size`).

Alternative considered: overload the current `/params` endpoint with optional modes. Rejected because it keeps one endpoint doing incompatible jobs and makes the client code harder to reason about.

### 3. Classify parameter rows in the imports route using the existing classifier

The imports route will reuse `ParamClassifier` to derive `stage` and `category` from `param_name` and `file_type`, and will derive `param_group` from the same role-prefix rules already used elsewhere.

Alternative considered: keep the import-detail page on naive string grouping and only page rows. Rejected because the project already has semantic grouping logic and not using it would preserve the “large flat table” problem.

### 4. Treat raw BSG parameter rows as secondary in parameter browsing

The dedicated `BSG` tab remains the primary BSG view. The default parameter summary and parameter facets will exclude `BSG` rows to avoid duplicating the same dataset in two tabs. If needed, explicit `file_type=BSG` requests can still be supported later, but the default user path should not start there.

Alternative considered: leave BSG inside the main parameter browser. Rejected because it adds noise and weakens the distinction between normalized detail tabs.

### 5. Refactor the UI into summary-first, tab-lazy loading

The detail page will:
- fetch summary and param facets on entry,
- render dataset overview cards and guided filters,
- fetch parameter rows only for the selected parameter view,
- fetch APP/BSG/RPM only when their tab is opened.

Alternative considered: keep the current `Promise.all` fetch and only add a summary panel. Rejected because it does not address payload size or time-to-orientation.

## Risks / Trade-offs

- More backend query paths → Mitigation: keep logic inside `web/routes/imports.py` and reuse helper functions for grouping/classification.
- Facet queries may still scan many rows for large imports → Mitigation: scope every query by `recipe_import_id` and use the existing `(recipe_import_id, file_type, param_name)` index.
- Frontend state becomes more complex than a single payload → Mitigation: separate summary state, params state, and per-tab lazy-load state explicitly.
- Excluding BSG from the default parameter browser may surprise existing users → Mitigation: keep the dedicated BSG tab visible and call out section counts in the summary.
