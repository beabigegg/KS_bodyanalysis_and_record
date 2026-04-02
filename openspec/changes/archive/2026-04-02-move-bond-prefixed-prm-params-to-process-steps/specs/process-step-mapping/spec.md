## MODIFIED Requirements

### Requirement: CSV-to-JSON conversion script
The system SHALL provide a conversion script that transforms `K&S_Recipe_Organized_by_Process.csv` into `web/config/process_step_lookup.json`.

#### Scenario: Convert CSV to JSON
- **WHEN** the user runs the conversion script with the CSV path as input
- **THEN** the script SHALL produce a JSON file where each key is a `param_name` and the value is an object containing `process_step`, `stage`, `category`, `family`, `feature`, `description`, and `tunable` fields

#### Scenario: Duplicate param_name in CSV
- **WHEN** the CSV contains duplicate `param_name` entries (e.g. across different param_groups)
- **THEN** the script SHALL keep the first occurrence and log a warning for duplicates

#### Scenario: Bond1-prefixed parameter does not remain in system monitoring
- **WHEN** the conversion script encounters a `param_name` with a `Bond1` prefix and the source row's `process_step_logic` is `7. 系統/監控/其他 (System & Monitoring)`
- **THEN** the script SHALL write `process_step = "2. BOND1 相關 / BUMP (First Bond)"` for that lookup entry

#### Scenario: Bump-prefixed parameter does not remain in system monitoring
- **WHEN** the conversion script encounters a `param_name` with a `Bump` prefix and the source row's `process_step_logic` is `7. 系統/監控/其他 (System & Monitoring)`
- **THEN** the script SHALL write `process_step = "2. BOND1 相關 / BUMP (First Bond)"` for that lookup entry

#### Scenario: Bond2-prefixed parameter does not remain in system monitoring
- **WHEN** the conversion script encounters a `param_name` with a `Bond2` prefix and the source row's `process_step_logic` is `7. 系統/監控/其他 (System & Monitoring)`
- **THEN** the script SHALL write `process_step = "6. BOND2 相關 (Second Bond / Tail)"` for that lookup entry

### Requirement: Process-step lookup has highest classification priority
The system SHALL query the process-step lookup before keyword mapping and regex semantics. When a match is found, lookup values SHALL override keyword-derived stage/category values for non-empty fields only.

#### Scenario: Lookup hit returns process_step and overrides stage
- **WHEN** `param_name = "parms/Bond1_Force_Seg_01"` and lookup contains an entry with `process_step = "2. BOND1 相關 / BUMP (First Bond)"` and `stage = "Bond1"`
- **THEN** the classifier SHALL return `process_step = "2. BOND1 相關 / BUMP (First Bond)"` and `stage = "Bond1"`

#### Scenario: Lookup hit with empty category preserves keyword result
- **WHEN** the lookup entry for a param_name has an empty `category` value
- **THEN** the classifier SHALL use the category from keyword mapping instead

#### Scenario: Lookup miss falls back to existing logic
- **WHEN** `param_name` is not found in the lookup dictionary
- **THEN** the classifier SHALL fall back to keyword mapping and regex semantics, returning `process_step = None`

#### Scenario: Bond-prefixed lookup hit does not expose system monitoring fallback
- **WHEN** `param_name` has a `Bond1`, `Bump`, or `Bond2` prefix and the lookup contains a corrected bond-related process-step entry for that parameter
- **THEN** the classifier SHALL return the corrected bond-related `process_step` instead of `7. 系統/監控/其他 (System & Monitoring)`
