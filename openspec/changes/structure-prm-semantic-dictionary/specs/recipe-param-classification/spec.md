## MODIFIED Requirements

### Requirement: Classify param_name into stage and category
The system SHALL classify PRM parameters using reference-aligned parameter classes and subgroup categories, while also exposing richer semantic metadata for documented PRM families.

#### Scenario: Bond1 force parameter maps to bond1 force
- **WHEN** `param_name = "parms/B1_Force_Seg_01"`
- **THEN** the classifier SHALL return `stage = "bond1"` and `category = "force"`

#### Scenario: Ball formation parameter maps to bond1 ball_efo
- **WHEN** `param_name = "parms/EFO_Power"`
- **THEN** the classifier SHALL return `stage = "bond1"` and `category = "ball_efo"`

#### Scenario: Bump parameter maps to bump force
- **WHEN** `param_name = "parms/Bump_Force_Seg_01"`
- **THEN** the classifier SHALL return `stage = "bump"` and `category = "force"`

#### Scenario: Loop balance parameter maps to loop balance
- **WHEN** `param_name = "parms/Bal_Loop_Percent"`
- **THEN** the classifier SHALL return `stage = "loop"` and `category = "balance"`

#### Scenario: Bond2 tail scrub parameter maps to bond2 tail_scrub
- **WHEN** `param_name = "parms/Tail_Scrub_Force"`
- **THEN** the classifier SHALL return `stage = "bond2"` and `category = "tail_scrub"`

#### Scenario: BITS parameter maps to bits_other
- **WHEN** `param_name = "parms/NSOP_Sensitivity"`
- **THEN** the classifier SHALL return `stage = "bits_other"` and `category = "nsop"`

#### Scenario: Dictionary-backed PRM family returns richer semantics
- **WHEN** `param_name = "parms/SF3_Rtn_Control"`
- **THEN** the classifier SHALL return semantic metadata including `family = "safety_fence"`, `feature = "return_control"`, and a human-readable description

#### Scenario: LF and MAG remain unclassified
- **WHEN** `file_type` is `LF` or `MAG`
- **THEN** the classifier SHALL return no PRM semantic classification

#### Scenario: Unknown prefix falls back to _unmapped
- **WHEN** the PRM prefix is not covered by the documented mapping, such as `XYZ_SomeParam`
- **THEN** the classifier SHALL return `stage = "_unmapped"` and `category = "xyz"`
