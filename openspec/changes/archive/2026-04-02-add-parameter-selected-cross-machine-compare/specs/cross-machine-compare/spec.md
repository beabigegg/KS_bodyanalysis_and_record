## ADDED Requirements

### Requirement: Parameter selection step before compare
The system SHALL require users to choose the parameter scope after selecting imports and before loading compare results.

#### Scenario: Compare flow pauses at parameter selection
- **WHEN** the user selects two or more imports and starts a cross-machine compare
- **THEN** the UI SHALL open a parameter selection step for those imports instead of immediately requesting compare results

#### Scenario: Import changes invalidate stale parameter selection
- **WHEN** the selected import set changes after parameters have been chosen
- **THEN** the system SHALL clear the previous parameter selection
- **AND** the user SHALL be required to choose parameters again before compare can run

### Requirement: Parameter diff results honor selected scope
The system SHALL limit parameter diff output to the user-selected parameter keys while continuing to compare the chosen imports.

#### Scenario: Compare selected parameter keys
- **WHEN** the user submits compare with a set of selected `(file_type, param_name)` keys
- **THEN** the `params` compare section SHALL include only rows whose keys are in that selection
- **AND** a selected parameter that is missing on one or more imports SHALL still be returned as a diff row

#### Scenario: Non-parameter sections remain available
- **WHEN** a compare session is created from selected imports and selected parameters
- **THEN** the UI SHALL continue to provide APP, BSG, RPM Limits, and RPM Reference sections for the same import set
