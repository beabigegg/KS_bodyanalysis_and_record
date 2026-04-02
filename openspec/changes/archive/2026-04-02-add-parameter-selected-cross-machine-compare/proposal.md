## Why

The current Cross-Machine Compare flow runs immediately after machine selection and returns the full parameter diff set. That makes large compares noisy, prevents users from narrowing the comparison to the parameters they actually care about, and diverges from the classification-first browsing flow already used in Recipe Import Records.

## What Changes

- Change Cross-Machine Compare into a two-step workflow: select imports, then select the parameter items to compare, then run the compare.
- Add a compare parameter-selection view that reuses the Recipe Import Records parameter browsing model, including file-type-first navigation and file-type-aware classification filters.
- Add backend support to build a compare parameter catalog across the selected imports and accept explicit selected parameter keys when generating the `params` compare section.
- Keep existing APP, BSG, RPM Limits, and RPM Reference compare sections available for the selected imports while scoping the parameter diff section to the chosen parameter items.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cross-machine-compare`: compare must pause at a parameter-selection step and only diff the selected parameter items.
- `param-browser`: compare parameter selection must reuse the same classification-first browsing model used in Recipe Import Records parameter view.
- `webui-backend`: compare APIs must provide a parameter catalog for selected imports and accept selected parameter keys in compare requests.

## Impact

- Frontend compare workflow in `web/frontend/src/pages/ComparePage.tsx` and related compare table/types modules
- Backend compare APIs in `web/routes/compare.py`, likely with shared semantic parameter helpers reused from import browsing
- Automated coverage for compare API behavior and the new parameter-selection flow
