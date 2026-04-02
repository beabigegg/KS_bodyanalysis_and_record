## Context

`ComparePage.tsx` currently lets the user filter imports, pick machines, and immediately post `POST /api/compare`. The request only scopes parameter rows with coarse controls like `file_type` and `show_all`, so the page has no place to let users choose the exact parameter items they want to inspect.

The project already has a richer parameter-browsing model in Recipe Import Records. `ImportDetailPage.tsx` starts from file type, uses semantic metadata such as `param_group` and `process_step`, and applies file-type-aware classification rules. The compare flow should reuse that model instead of inventing a second parameter-browsing pattern.

The existing compare diff logic already pivots parameter rows on `(file_type, param_name)`, which is a stable cross-import key and can serve as the selection identifier for scoped compares.

## Goals / Non-Goals

**Goals:**
- Add a two-step compare workflow where users must choose parameters after choosing imports.
- Reuse the Recipe Import Records classification model so compare parameter selection feels familiar and predictable.
- Scope parameter diff output to explicit selected parameter keys while preserving missing-value diffs across imports.
- Keep existing non-parameter compare sections available for the same selected imports.

**Non-Goals:**
- Redesign APP, BSG, or RPM compare behavior beyond preserving access after the new selection step.
- Change parameter-classification semantics or the underlying classifier rules.
- Introduce database schema changes or data migrations.

## Decisions

### Decision 1: Add a compare-specific parameter catalog endpoint

Add `POST /api/compare/params/catalog` to build a paged union parameter catalog for the currently selected imports. The response should include file-type counts, meaningful semantic facets for the active filter context, and candidate parameter rows with the metadata needed to render the selection table.

This keeps compare-specific aggregation out of the single-import browsing endpoints and avoids forcing a complex multi-import selection workflow into query-string-only APIs.

Alternative considered: reuse `/api/imports/{id}/params` and merge results in the client. Rejected because the endpoint is single-import by design and cannot accurately represent union coverage or facet counts across multiple selected imports.

### Decision 2: Represent selections with stable parameter keys

Send selected parameters to `POST /api/compare` as `(file_type, param_name)` keys. That matches the current compare pivot key, keeps the request independent from per-import row IDs, and still allows the compare result to show missing values on machines where a selected parameter does not exist.

Alternative considered: send per-import parameter row IDs. Rejected because row IDs are not stable across imports and would break the cross-machine concept of "the same parameter."

### Decision 3: Reuse classification visibility rules and clear stale selections

The compare parameter-selection UI should reuse the same file-type-aware classification visibility and labels used by Recipe Import Records. When the selected import set changes, the UI should clear the previous parameter selection and require the user to pick parameters again so the compare scope always matches the active imports.

Alternative considered: keep old selections when imports change. Rejected because the same `(file_type, param_name)` selection can mean materially different coverage after import changes, which would make the compare scope stale and misleading.

## Risks / Trade-offs

- [Catalog query cost] Aggregating a union parameter catalog across multiple imports can be heavier than the current direct compare call. -> Limit catalog generation to the selected imports, exclude BSG from the parameter catalog, and page candidate rows.
- [Stale selections] Users can change imports after building a selection, which makes the old selection unreliable. -> Reset parameter selections whenever the import set changes and show the user that reselection is required.
- [Large request payloads] Explicit parameter selections can grow large for broad compares. -> Use compact `(file_type, param_name)` key objects and keep the first implementation focused on interactive selection rather than bulk-export semantics.
