## MODIFIED Requirements

### Requirement: REST API endpoints
The system SHALL expose REST APIs for import browsing, compare, trend, R2R workflows, and import record deletion.

#### Scenario: List imports endpoint
- **WHEN** a client requests `GET /api/imports`
- **THEN** the system SHALL return recipe import records with supported list filters

#### Scenario: Import detail summary endpoint
- **WHEN** a client requests `GET /api/imports/{id}/summary`
- **THEN** the system SHALL return counts for parameter rows, file types, APP availability, BSG rows, RPM limits, and RPM reference rows for that import

#### Scenario: Import parameter facets endpoint
- **WHEN** a client requests `GET /api/imports/{id}/param-facets`
- **THEN** the system SHALL return available file types, parameter groups, stages, categories, and richer PRM semantic facets such as family and feature derived from that import's stored parameter semantics

#### Scenario: Filtered import params endpoint
- **WHEN** a client requests `GET /api/imports/{id}/params` with filters such as `file_type`, `param_group`, `stage`, `category`, `family`, `feature`, `search`, `page`, or `page_size`
- **THEN** the system SHALL return matching parameter rows together with their semantic metadata, including PRM fields such as `family`, `feature`, `instance`, `description`, and `tunable` when available, and SHALL include total row count for the filtered result set

#### Scenario: Delete single import endpoint
- **WHEN** a client sends `DELETE /api/imports/{import_id}`
- **THEN** the system SHALL delete the import record and all associated data and return a success response

#### Scenario: Batch delete imports endpoint
- **WHEN** a client sends `DELETE /api/imports/batch` with `{"ids": [...]}`
- **THEN** the system SHALL delete all specified import records and their associated data and return the count of deleted records

#### Scenario: Compare endpoint
- **WHEN** a client posts to `POST /api/compare` with selected import ids
- **THEN** the system SHALL return comparison data for the requested section

#### Scenario: Compare endpoint supports section paging
- **WHEN** a client posts to `POST /api/compare` with `section`, `page`, and `page_size`
- **THEN** the system SHALL return shared compare context plus only the requested section rows for that page

#### Scenario: Parameter compare filters remain supported
- **WHEN** a client requests the `params` compare section with a `file_type` filter
- **THEN** the system SHALL apply that filter before building parameter diff rows

#### Scenario: Trend endpoint
- **WHEN** a client requests `GET /api/trend`
- **THEN** the system SHALL return trend data for the requested machine, product, and parameter context

#### Scenario: R2R statistics endpoint
- **WHEN** a client requests `GET /api/r2r/stats`
- **THEN** the system SHALL return SPC-oriented statistics such as mean, standard deviation, and capability metrics

### Requirement: Database connection management
The system SHALL use shared SQLAlchemy schema definitions and support both read and write database access for web APIs.

#### Scenario: Share schema with parser
- **WHEN** the application starts
- **THEN** the API layer SHALL use the shared schema definitions from `db/schema.py`

#### Scenario: Read-only access for query endpoints
- **WHEN** API routes query application data
- **THEN** they SHALL rely on read-oriented database access patterns

#### Scenario: Write access for delete endpoints
- **WHEN** delete API routes are invoked
- **THEN** they SHALL use a writable database connection with transaction support
