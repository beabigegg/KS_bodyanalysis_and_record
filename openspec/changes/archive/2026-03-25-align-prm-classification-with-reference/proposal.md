## Why

The current PRM classifier is mostly prefix-driven and leaves about half of real PRM parameters in `_unmapped`. We now have a K&S-specific prefix and keyword reference, so this is the right point to align classification semantics with actual machine documentation instead of continuing to grow ad hoc heuristics.

## What Changes

- Rework PRM classification to follow the documented parameter classes and subgroup keywords from the K&S reference memo.
- Change PRM `stage` values to represent stable parameter classes instead of the current partial prefix taxonomy.
- Change PRM `category` values to represent subgroup or function families inferred from documented keywords and context.
- Keep non-PRM classification behavior intact unless needed for compatibility.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `recipe-param-classification`: PRM stage/category mapping changes from limited prefix heuristics to K&S reference-aligned parameter class and subgroup classification.

## Impact

- Backend/shared logic: `web/utils/param_classifier.py`
- Tests: `tests/test_param_classifier.py` and any compare/import route tests that assert PRM classification values
- UI/API consumers: compare and import-detail pages will display the updated stage/category values without changing endpoint shapes
