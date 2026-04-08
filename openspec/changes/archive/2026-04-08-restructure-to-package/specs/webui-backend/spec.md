## MODIFIED Requirements

### Requirement: FastAPI application with .env configuration
The system SHALL run as a FastAPI application and load runtime configuration from `.env`.

#### Scenario: Load configuration from unified config
- **WHEN** the application starts
- **THEN** it SHALL load all settings from `ksbody.config.get_settings()` instead of a separate `web/settings.py`

#### Scenario: Serve frontend as static files
- **WHEN** the web application is deployed as a single service
- **THEN** FastAPI SHALL serve the built frontend bundle from `ksbody/web/frontend/dist/`

### Requirement: Database connection management
The system SHALL use shared SQLAlchemy schema definitions and support both read and write database access for web APIs.

#### Scenario: Share schema with parser
- **WHEN** the application starts
- **THEN** the API layer SHALL use the shared schema definitions from `ksbody.db.schema` via standard package imports (no sys.path hack)

#### Scenario: Read-only access for query endpoints
- **WHEN** API routes query application data
- **THEN** they SHALL rely on read-oriented database access patterns

#### Scenario: Write access for delete endpoints
- **WHEN** delete API routes are invoked
- **THEN** they SHALL use a writable database connection with transaction support

### Requirement: Package-based import paths
Web 模組 SHALL 使用 `ksbody.web.*` 作為 import 路徑前綴。

#### Scenario: Route modules use package imports
- **WHEN** `app.py` 引入 route modules
- **THEN** 使用 `from ksbody.web.routes.compare import router` 等完整路徑

#### Scenario: No sys.path manipulation
- **WHEN** web 模組需要存取 `ksbody.db.schema`
- **THEN** 直接使用 `from ksbody.db.schema import metadata`，不使用 `sys.path.insert` hack
