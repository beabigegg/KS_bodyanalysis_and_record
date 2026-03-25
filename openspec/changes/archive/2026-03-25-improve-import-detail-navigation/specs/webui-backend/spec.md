## ADDED Requirements

### Requirement: Import detail summary endpoint
The backend SHALL provide a summary endpoint for a single import that reports dataset availability and counts needed for summary-first browsing.

#### Scenario: Summary includes section counts
- **WHEN** a client requests `GET /api/imports/{id}/summary`
- **THEN** the system SHALL return counts for parameter rows, parameter file types, APP availability, BSG rows, RPM limits, and RPM reference rows for that import

#### Scenario: Missing import returns not found
- **WHEN** a client requests the summary endpoint for an import id that does not exist
- **THEN** the system SHALL return HTTP 404

### Requirement: Import parameter facets endpoint
The backend SHALL provide a facets endpoint for a single import that returns guided filter values for parameter browsing.

#### Scenario: Facets reflect stored parameter semantics
- **WHEN** a client requests `GET /api/imports/{id}/param-facets`
- **THEN** the system SHALL return available file types, parameter groups, stages, and categories derived from that import's stored parameter rows

### Requirement: Import parameter browsing endpoint supports paging
The backend SHALL support paged and filtered parameter browsing for a single import.

#### Scenario: Filtered parameter page is returned
- **WHEN** a client requests `GET /api/imports/{id}/params` with filters such as `file_type`, `param_group`, `stage`, `category`, `search`, `page`, or `page_size`
- **THEN** the system SHALL return only rows matching those filters and SHALL include total row count for the filtered result set

#### Scenario: Parameter rows include semantic metadata
- **WHEN** the backend returns parameter rows for import browsing
- **THEN** each row SHALL include the derived `param_group`, `stage`, and `category` fields used by the client for navigation
