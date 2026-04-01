## Requirements

### Requirement: Single import record deletion
The system SHALL allow deletion of a single recipe import record and all its associated data.

#### Scenario: Delete single import via API
- **WHEN** a client sends `DELETE /api/imports/{import_id}` with a valid import ID
- **THEN** the system SHALL delete the import record and all related rows in recipe_params, recipe_app_spec, recipe_bsg, recipe_rpm_limits, recipe_rpm_reference, and recipe_wir_group_map within a single transaction, and return a success response

#### Scenario: Delete non-existent import
- **WHEN** a client sends `DELETE /api/imports/{import_id}` with an ID that does not exist
- **THEN** the system SHALL return HTTP 404 with an error message

#### Scenario: Single delete from UI
- **WHEN** the user clicks the delete button on an import record row
- **THEN** the system SHALL show a confirmation dialog, and upon confirmation, call the delete API and refresh the list

### Requirement: Batch import record deletion
The system SHALL allow deletion of multiple recipe import records in a single operation.

#### Scenario: Batch delete via API
- **WHEN** a client sends `DELETE /api/imports/batch` with a JSON body containing `{"ids": [id1, id2, ...]}`
- **THEN** the system SHALL delete all specified import records and their associated data within a single transaction, and return the count of deleted records

#### Scenario: Batch delete with empty list
- **WHEN** a client sends `DELETE /api/imports/batch` with an empty ids list
- **THEN** the system SHALL return HTTP 400 with an error message

#### Scenario: Batch delete with partial invalid IDs
- **WHEN** a client sends `DELETE /api/imports/batch` with some IDs that do not exist
- **THEN** the system SHALL delete only the records that exist and return the count of actually deleted records

### Requirement: Import list selection UI
The system SHALL provide checkbox-based selection for batch operations on the import list page.

#### Scenario: Select individual records
- **WHEN** the user clicks a checkbox on an import record row
- **THEN** that record SHALL be marked as selected and the batch action bar SHALL appear showing the selected count

#### Scenario: Select all records on current page
- **WHEN** the user clicks the header checkbox
- **THEN** all records on the current page SHALL be selected

#### Scenario: Deselect all
- **WHEN** the user clicks the header checkbox while all records are selected
- **THEN** all records SHALL be deselected and the batch action bar SHALL be hidden

#### Scenario: Batch delete from UI
- **WHEN** the user clicks the batch delete button with records selected
- **THEN** the system SHALL show a confirmation dialog displaying the count of selected records, and upon confirmation, call the batch delete API, clear selections, and refresh the list

#### Scenario: Selection cleared on page change
- **WHEN** the user navigates to a different page or applies new filters
- **THEN** the current selection SHALL be cleared
