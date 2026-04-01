## MODIFIED Requirements

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
