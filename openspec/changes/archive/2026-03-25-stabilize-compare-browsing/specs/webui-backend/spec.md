## ADDED Requirements

### Requirement: Compare endpoint supports section-based paging
The backend SHALL support section-based and paged compare responses so the UI can browse large compare results safely.

#### Scenario: Active compare section is requested
- **WHEN** a client posts to `POST /api/compare` with `section`, `page`, and `page_size`
- **THEN** the system SHALL return shared compare context plus only the requested section rows for that page

#### Scenario: Parameter compare filters remain supported
- **WHEN** a client requests the `params` compare section with a `file_type` filter
- **THEN** the system SHALL apply that filter before building the parameter diff rows
