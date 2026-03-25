## 1. Reference-aligned PRM classification

- [x] 1.1 Rework `web/utils/param_classifier.py` so PRM stage maps to documented parameter classes
- [x] 1.2 Add keyword/context rules so PRM category maps to documented subgroup families
- [x] 1.3 Preserve current non-PRM classification behavior and explicit `_unmapped` fallback

## 2. Verification

- [x] 2.1 Update classifier tests to the new stage/category semantics
- [x] 2.2 Run targeted tests for classifier and affected compare/import routes
- [x] 2.3 Measure sample PRM coverage before/after to confirm `_unmapped` decreases materially
