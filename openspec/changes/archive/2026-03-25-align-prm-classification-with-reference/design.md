## Context

The current `ParamClassifier` treats PRM classification as a small static prefix map. That was enough to bootstrap compare grouping, but sample analysis shows that roughly half of PRM rows still fall into `_unmapped`. The reference memo provided by the user describes a richer model:
- parameter classes such as Bond1/Ball, Bond2, Loop, and BITS/Other
- subgroup families such as Force, USG, Scrub, Tail, Balance, and 2nd Approach
- several categories that require both prefix and keyword/context, not prefix alone

The classifier should move toward that documented model while preserving the same return contract: `(stage, category)`.

## Goals / Non-Goals

**Goals:**
- Improve PRM coverage using the K&S memo as the source of truth for stage/category semantics.
- Make `stage` correspond to stable parameter classes instead of the current mixed taxonomy.
- Make `category` correspond to subgroup/function buckets that are understandable in the UI.
- Keep the implementation deterministic and testable from raw `param_name` values.

**Non-Goals:**
- Build a perfect parser for every premium or undocumented PRM field.
- Change database schema or API response shapes.
- Rework non-PRM role-based keyword classification beyond compatibility fixes.

## Decisions

### 1. Define stage as parameter class

For PRM rows, `stage` will represent a top-level parameter class derived from the memo:
- `bond1_ball`
- `bond2`
- `loop`
- `bits_other`
- `quick_adjust`
- `_unmapped` fallback

This is more stable than the previous `bond1` / `ball_formation` / `loop` mix, and better matches how the machine UI organizes PRM content.

### 2. Derive category from subgroup keywords before falling back to prefix

Classification will inspect the normalized PP body for documented keyword families such as:
- Bond1/Ball: `force`, `usg`, `scrub`, `common`, `misc`
- Bond2: `force`, `usg`, `scrub`, `tail_scrub`, `misc`
- Loop: `main`, `shaping`, `balance`, `second_approach`
- Bits/Other: `bits`, `nsop`, `nsol_shtl`, `misc`

Prefix-only rules remain as helpers, but keyword-family matching becomes the primary source for category assignment.

### 3. Preserve explicit fallbacks for unknown prefixes

Unknown PRM prefixes will still return `("_unmapped", <normalized-prefix>)`. This keeps the current diagnostic value and prevents silent misclassification.

## Risks / Trade-offs

- Some previously stable labels will change in the UI → Mitigation: keep field names the same and update tests to the new semantic expectations.
- Keyword rules may still misclassify ambiguous names → Mitigation: prefer `_unmapped` over forcing a weak guess.
- Premium/rare parameters may remain partially uncovered → Mitigation: keep the classifier table-driven so new rules can be added incrementally from observed data.
