## Requirements

### Requirement: Browse recipe import records
The system SHALL let users browse imported recipe records with machine and product filters.

#### Scenario: View import list with filters
- **WHEN** the user opens the import browsing page
- **THEN** the UI SHALL list recipe imports with fields such as machine type, machine id, product type, BOP, wafer PN, recipe time, and import time

#### Scenario: Filter by machine and product
- **WHEN** the user applies machine or product filters
- **THEN** the system SHALL narrow the import list to matching imports

#### Scenario: Search by keyword
- **WHEN** the user searches by keyword
- **THEN** the system SHALL match import records by fields such as `product_type`, `bop`, `wafer_pn`, and `recipe_name`

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

### Requirement: Guided parameter facets
The system SHALL expose guided parameter facets derived from stored parameter semantics so users can narrow large imports without relying on raw text search alone.

#### Scenario: File type and semantic facet options are available
- **WHEN** a user enters the parameter browsing view for an import
- **THEN** the system SHALL provide available file types, parameter groups, stages, categories, and richer PRM semantics such as family and feature for that import

#### Scenario: Parameter facet options reflect current filter context
- **WHEN** the user applies one or more parameter filters
- **THEN** the available facet options and counts SHALL update to reflect the remaining matching dataset

#### Scenario: PRM browser can group documented unmapped families
- **WHEN** the user browses PRM parameters such as `SF*` or `SL*`
- **THEN** the browser SHALL let the user organize those rows by semantic family and feature instead of leaving them in an undifferentiated unmapped bucket

### Requirement: Export parameters
The system SHALL let users export the currently filtered parameter dataset as CSV.

#### Scenario: Export filtered parameters
- **WHEN** the user exports parameter rows from the detail page
- **THEN** the exported CSV SHALL contain the currently filtered parameter dataset
