## ADDED Requirements

### Requirement: Dictionary-driven PRM semantics
The system SHALL support a dictionary-driven semantic layer for PRM parameters so documented unmapped families can be classified consistently.

#### Scenario: Safety Fence parameter resolves through dictionary
- **WHEN** `param_name = "parms/SF10_Pullout_Dist"`
- **THEN** the system SHALL classify it with semantic data including `family = "safety_fence"` and `feature = "pullout_dist"`

#### Scenario: Smart Loop parameter resolves through dictionary
- **WHEN** `param_name = "parms/SL3_Scalar"`
- **THEN** the system SHALL classify it with semantic data including `family = "smart_loop"` and `feature = "scalar"`

#### Scenario: Regex rule captures indexed instance
- **WHEN** a parameter name matches an indexed family pattern such as `SF10_Pullout_Dist`
- **THEN** the semantic result SHALL include an `instance` value derived from the matched group

#### Scenario: Internal conversion flag is marked non-tunable
- **WHEN** a PRM parameter is classified as an internal compatibility flag such as a `_Conv` parameter
- **THEN** the semantic result SHALL mark `tunable = false`
