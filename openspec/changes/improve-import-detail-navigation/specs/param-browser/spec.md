## ADDED Requirements

### Requirement: Summary-first import detail browsing
The system SHALL present import detail as a summary-first browsing flow instead of forcing users to load all parameter rows before they can orient themselves.

#### Scenario: Import detail opens with section overview
- **WHEN** a user opens an import detail page
- **THEN** the system SHALL show top-level counts for parameter data and specialized sections before loading parameter row tables

#### Scenario: Parameter data is browsed incrementally
- **WHEN** a user filters by file type, parameter group, stage, category, or keyword
- **THEN** the system SHALL request only the matching parameter slice for the active page instead of loading the full import parameter dataset

### Requirement: Guided parameter facets
The system SHALL expose guided parameter facets derived from stored parameter semantics so users can narrow large imports without relying on raw text search alone.

#### Scenario: File type and semantic facet options are available
- **WHEN** a user enters the parameter browsing view for an import
- **THEN** the system SHALL provide available file types, parameter groups, stages, and categories for that import

#### Scenario: Dedicated BSG detail remains primary
- **WHEN** an import contains BSG data
- **THEN** the default parameter browsing summary SHALL avoid emphasizing raw BSG parameter rows and SHALL keep the dedicated BSG detail view as the primary BSG entry point
