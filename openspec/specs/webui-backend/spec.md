## ADDED Requirements

### Requirement: FastAPI application with .env configuration
The system SHALL run as a FastAPI application and load runtime configuration from `.env`.

#### Scenario: Load configuration from .env
- **WHEN** the application starts
- **THEN** it SHALL load environment values such as app mode, port, and database connection settings from `.env`

#### Scenario: Serve frontend as static files
- **WHEN** the web application is deployed as a single service
- **THEN** FastAPI SHALL serve the built frontend bundle together with the API

### Requirement: REST API endpoints
The system SHALL expose REST APIs for import browsing, compare, trend, and R2R workflows.

#### Scenario: List imports endpoint
- **WHEN** a client requests `GET /api/imports`
- **THEN** the system SHALL return recipe import records with supported list filters

#### Scenario: Import detail summary endpoint
- **WHEN** a client requests `GET /api/imports/{id}/summary`
- **THEN** the system SHALL return counts for parameter rows, file types, APP availability, BSG rows, RPM limits, and RPM reference rows for that import

#### Scenario: Import parameter facets endpoint
- **WHEN** a client requests `GET /api/imports/{id}/param-facets`
- **THEN** the system SHALL return available file types, parameter groups, stages, and categories derived from that import's stored parameter semantics

#### Scenario: Filtered import params endpoint
- **WHEN** a client requests `GET /api/imports/{id}/params` with filters such as `file_type`, `param_group`, `stage`, `category`, `search`, `page`, or `page_size`
- **THEN** the system SHALL return only rows matching those filters and SHALL include total row count for the filtered result set

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
The system SHALL use shared SQLAlchemy schema definitions and read-only database access for web APIs.

#### Scenario: Share schema with parser
- **WHEN** the application starts
- **THEN** the API layer SHALL use the shared schema definitions from `db/schema.py`

#### Scenario: Read-only access
- **WHEN** API routes query application data
- **THEN** they SHALL rely on read-oriented database access patterns

### Requirement: API response format
The system SHALL return consistent JSON envelopes for successful and error responses.

#### Scenario: Successful response
- **WHEN** an API request succeeds
- **THEN** the response SHALL use a JSON envelope such as `{"data": ..., "total": N}`

#### Scenario: Error response
- **WHEN** an API request fails
- **THEN** the response SHALL return an HTTP error with a JSON body describing the failure
