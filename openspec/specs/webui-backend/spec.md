## Requirements

### Requirement: FastAPI application with .env configuration
The system SHALL run as a FastAPI application and load runtime configuration from `.env`.

#### Scenario: Load configuration from .env
- **WHEN** the application starts
- **THEN** it SHALL load environment values such as app mode, port, and database connection settings from `.env`

#### Scenario: Serve frontend as static files
- **WHEN** the web application is deployed as a single service
- **THEN** FastAPI SHALL serve the built frontend bundle together with the API

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

### Requirement: API response format
The system SHALL return consistent JSON envelopes for successful and error responses.

#### Scenario: Successful response
- **WHEN** an API request succeeds
- **THEN** the response SHALL use a JSON envelope such as `{"data": ..., "total": N}`

#### Scenario: Error response
- **WHEN** an API request fails
- **THEN** the response SHALL return an HTTP error with a JSON body describing the failure

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
