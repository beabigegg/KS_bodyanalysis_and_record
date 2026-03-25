## Why

The compare workflow currently returns every diff section in one response and renders every result table at once. On larger KS recipe sets, that creates a very large payload and DOM tree, which is enough to freeze or crash the browser.

## What Changes

- Change compare data loading from "all sections at once" to "one section at a time".
- Add server-side pagination for compare result rows so the browser only renders a bounded slice.
- Update the compare page to fetch and render the active section lazily instead of mounting all diff tables together.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `cross-machine-compare`: Compare browsing changes from full-response rendering to section-based, paged browsing.
- `webui-backend`: The compare API changes to support section selection and paged responses for compare result rows.

## Impact

- Backend: `web/routes/compare.py`
- Frontend: `web/frontend/src/pages/ComparePage.tsx`, compare-related types and tables
- Tests: compare route tests need to verify section filtering and pagination
