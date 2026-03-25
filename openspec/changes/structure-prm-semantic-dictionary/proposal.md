## Why

The current PRM classification logic is still dominated by stage/category heuristics. That works for classic bond-stage parameters, but it breaks down for large unmapped families such as `SF*`, `SL*`, `GEN_*`, `Pro*`, and `_Conv` flags where the important meaning is the functional module, not just the process stage.

## What Changes

- Introduce a dictionary-driven PRM semantics layer that can classify parameters into richer semantic fields instead of relying only on prefix heuristics.
- Extend PRM semantic output with fields such as `family`, `feature`, `instance`, `description`, and `tunable` while keeping `stage` and `category` for compatibility.
- Add first-wave coverage for the high-value unmapped families documented in the project memo, including `SF*`, `SL*`, `GEN_*`, `Pro*`, `WBMS`, `Pull`, `Overbend`, `Lean`, `Rev*`, `Neck`, `TailTear`, and `_Conv` markers.
- Update import-detail browsing so PRM filters and grouping can use the new semantic fields instead of forcing all meaning into `stage/category`.

## Capabilities

### New Capabilities
- `prm-semantic-dictionary`: Dictionary-driven classification rules and semantic metadata for PRM parameters.

### Modified Capabilities
- `recipe-param-classification`: PRM classification output expands beyond `stage/category` and uses dictionary-backed rules for documented unmapped families.
- `param-browser`: Import detail browsing exposes and uses richer PRM semantic facets such as family and feature.
- `webui-backend`: Import parameter APIs return the enriched PRM semantic fields needed by the browser.

## Impact

- Affected code: `web/utils/param_classifier.py`, `web/routes/imports.py`, frontend import detail views, API types, and tests.
- New configuration/data asset for PRM semantic rules.
- Import browsing responses gain additional semantic fields for PRM rows.
