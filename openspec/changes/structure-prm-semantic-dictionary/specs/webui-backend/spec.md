## MODIFIED Requirements

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
- **THEN** the system SHALL return available file types, parameter groups, stages, categories, and richer PRM semantic facets such as family and feature derived from that import's stored parameter semantics

#### Scenario: Filtered import params endpoint
- **WHEN** a client requests `GET /api/imports/{id}/params`
- **THEN** the system SHALL return matching parameter rows together with their semantic metadata, including PRM fields such as `family`, `feature`, `instance`, `description`, and `tunable` when available
