## Requirements

### Requirement: Classify param_name into stage and category
The system SHALL classify PRM parameters using reference-aligned parameter classes and subgroup categories, while also exposing richer semantic metadata for documented PRM families and continuing to classify non-PRM roles with their existing keyword logic.

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

#### Scenario: Quick adjust parameter maps to quick_adjust
- **WHEN** `param_name = "parms/Bond_Adjust_Force"`
- **THEN** the classifier SHALL return `stage = "quick_adjust"` and `category = "bond"`

#### Scenario: PHY mag_handler keyword mapping
- **WHEN** `param_name = "mag_handler/IN_FIRST_SLOT"`
- **THEN** the classifier SHALL return `stage = None` and `category = "slot"`

#### Scenario: PHY workholder keyword mapping
- **WHEN** `param_name = "workholder/LOT_SEP_MODES"`
- **THEN** the classifier SHALL return `stage = None` and `category = "indexing"`

#### Scenario: REF die_ref keyword mapping
- **WHEN** `param_name = "die_ref/eyepoint_x_1"`
- **THEN** the classifier SHALL return `stage = None` and `category = "eyepoint"`

#### Scenario: REF lead_ref VLL category
- **WHEN** `param_name = "lead_ref/corridor_length"`
- **THEN** the classifier SHALL return `stage = None` and `category = "vll"`

#### Scenario: LF and MAG remain unclassified
- **WHEN** `file_type` is `LF` or `MAG`
- **THEN** the classifier SHALL return no PRM semantic classification

#### Scenario: HB temperature zone mapping
- **WHEN** `param_name` contains `preheat` and `file_type = "HB"`
- **THEN** the classifier SHALL return `stage = None` and `category = "preheat"`

#### Scenario: Unknown prefix falls back to _unmapped
- **WHEN** the PRM prefix is not covered by the documented mapping, such as `XYZ_SomeParam`
- **THEN** the classifier SHALL return `stage = "_unmapped"` and `category = "xyz"`
