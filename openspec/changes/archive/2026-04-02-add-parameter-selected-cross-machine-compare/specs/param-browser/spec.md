## ADDED Requirements

### Requirement: Compare parameter selection reuses classification-first browsing
The system SHALL present compare parameter selection with the same file-type-first and classification-aware browsing model used in Recipe Import Records parameter view.

#### Scenario: Compare selection starts from file type overview
- **WHEN** the user enters the parameter selection step for compare
- **THEN** the UI SHALL present available file types for the selected imports before asking the user to choose parameter rows

#### Scenario: Compare selection offers guided facets for the chosen file type
- **WHEN** the user narrows the compare parameter catalog
- **THEN** the system SHALL offer only the classification facets that are meaningful for the active file type, including `param_group` and `process_step` for `PRM`

#### Scenario: Compare selection can browse union parameter catalog
- **WHEN** a parameter exists on some selected imports but not others
- **THEN** the compare parameter selection view SHALL still list that parameter as a selectable item

### Requirement: Compare selection uses file-type-aware classification columns
The system SHALL apply the same file-type-specific classification column visibility rules in compare parameter selection as in import detail parameter browsing.

#### Scenario: PRM compare selection displays PRM classification columns
- **WHEN** the user views `PRM` parameters in compare selection
- **THEN** the selection table SHALL display `process_step`, `param_group`, `stage`, `category`, `family`, `feature`, `instance`, `tunable`, and `description`

#### Scenario: PHY and REF compare selection hide unsupported classification columns
- **WHEN** the user views `PHY` or `REF` parameters in compare selection
- **THEN** the selection table SHALL display `param_group`
- **AND** the selection table SHALL NOT display `process_step`, `stage`, `category`, `family`, `feature`, `instance`, `tunable`, or `description`

#### Scenario: Other file types hide all classification columns
- **WHEN** the user views parameters of file type `AIC`, `BND`, `HB`, `LF`, `LHM`, `MAG`, `PPC`, `VHM`, or `WIR` in compare selection
- **THEN** the selection table SHALL NOT display `process_step`, `param_group`, `stage`, `category`, `family`, `feature`, `instance`, `tunable`, or `description`
