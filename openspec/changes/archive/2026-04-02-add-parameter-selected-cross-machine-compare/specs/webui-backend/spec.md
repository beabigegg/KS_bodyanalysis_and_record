## ADDED Requirements

### Requirement: Compare parameter catalog endpoint
The system SHALL expose a compare-specific parameter catalog API derived from the selected imports.

#### Scenario: Return compare parameter catalog
- **WHEN** a client posts selected import ids to `POST /api/compare/params/catalog`
- **THEN** the system SHALL return a paged union of selectable `(file_type, param_name)` rows across those imports
- **AND** each catalog row SHALL include the semantic metadata needed for compare parameter browsing

#### Scenario: Return compare parameter facets
- **WHEN** a client applies file type or semantic filters to `POST /api/compare/params/catalog`
- **THEN** the system SHALL return facet counts and candidate rows for the remaining matching parameter catalog

#### Scenario: Catalog includes partially present parameters
- **WHEN** a parameter exists on some selected imports but not others
- **THEN** the catalog response SHALL still include that parameter as a selectable item

### Requirement: Compare endpoint supports selected parameter scope
The system SHALL allow parameter compare requests to be scoped to explicit selected parameter keys.

#### Scenario: Params section is filtered by selected parameter keys
- **WHEN** a client posts to `POST /api/compare` with `section = "params"` and `selected_params`
- **THEN** the system SHALL return only compare rows whose `(file_type, param_name)` keys are included in `selected_params`
- **AND** the existing `show_all`, `page`, `page_size`, and `file_type` behavior SHALL still apply

#### Scenario: Non-parameter sections ignore parameter scope
- **WHEN** a client posts to `POST /api/compare` for `app_spec`, `bsg`, `rpm_limits`, or `rpm_reference`
- **THEN** the system SHALL continue to compare those sections for the selected imports without requiring `selected_params`
