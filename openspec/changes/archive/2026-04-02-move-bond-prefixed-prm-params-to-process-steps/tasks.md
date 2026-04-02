## 1. Prefix-aware lookup correction

- [x] 1.1 Update `scripts/build_process_step_lookup.py` to remap `Bond1*` and `Bump*` parameters from `7. 系統/監控/其他 (System & Monitoring)` to `2. BOND1 相關 / BUMP (First Bond)` during lookup generation.
- [x] 1.2 Update `scripts/build_process_step_lookup.py` to remap `Bond2*` parameters from `7. 系統/監控/其他 (System & Monitoring)` to `6. BOND2 相關 (Second Bond / Tail)` during lookup generation.
- [x] 1.3 Keep the correction scoped so it only applies when the source process step is `System & Monitoring`, preserving more specific existing process-step values.

## 2. Regression coverage

- [x] 2.1 Add or update tests for lookup generation so `Bond1`, `Bump`, and `Bond2` prefixed rows no longer serialize to `System & Monitoring`.
- [x] 2.2 Add or update classifier tests to verify lookup-covered bond-prefixed PRM parameters return the corrected `process_step`.

## 3. Regenerate and verify lookup data

- [ ] 3.1 Rebuild `web/config/process_step_lookup.json` from `K&S_Recipe_Organized_by_Process.csv` using the updated script.
- [ ] 3.2 Verify representative corrected entries in `web/config/process_step_lookup.json` and confirm no targeted bond-prefixed regressions remain in `System & Monitoring`.
