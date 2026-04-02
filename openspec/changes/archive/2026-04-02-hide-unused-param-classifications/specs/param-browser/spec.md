## MODIFIED Requirements

### Requirement: Summary-first import detail browsing
The system SHALL present import detail as a summary-first browsing flow instead of forcing users to load all parameter rows before they can orient themselves. The parameter table SHALL only display classification columns that are meaningful for the current file type.

#### Scenario: Import detail opens with section overview
- **WHEN** a user opens an import detail page
- **THEN** the system SHALL show top-level counts for parameter data and specialized sections before loading parameter row tables

#### Scenario: Parameter data is browsed incrementally
- **WHEN** a user filters by file type, parameter group, stage, category, or keyword
- **THEN** the system SHALL narrow the displayed parameter dataset without forcing the user to scan the entire recipe payload at once

#### Scenario: PRM parameters display all classification columns
- **WHEN** a user views PRM file type parameters
- **THEN** the table SHALL display param_group, stage, category, family, feature, instance, tunable, and description columns

#### Scenario: Non-PRM non-REF non-PHY parameters hide all classification columns
- **WHEN** a user views parameters of file type AIC, BND, HB, LF, LHM, MAG, PPC, VHM, or WIR
- **THEN** the table SHALL NOT display param_group, stage, category, family, feature, instance, tunable, or description columns

#### Scenario: PHY and REF parameters hide classification columns except param_group
- **WHEN** a user views parameters of file type PHY or REF
- **THEN** the table SHALL display param_group but SHALL NOT display stage, category, family, feature, instance, tunable, or description columns

#### Scenario: Compare mode hides unused classification columns
- **WHEN** a user compares parameters across imports
- **THEN** the comparison table SHALL hide classification columns that are empty for all displayed rows
