## Context

The current project already classifies PRM parameters into `stage` and `category`, and the import-detail page can filter by those two dimensions. That model works for bond/loop-style names such as `B1_Force_Seg_01`, but it does not express the meaning of many documented unmapped parameters where the dominant axis is a feature family such as Safety Fence, Smart Loop, Tail Tear, or ProBond.

The user has now provided a much more complete interpretation of the unmapped parameter space. Those meanings are not encoded in BND and should not be inferred from wire-group metadata. They belong in a dedicated PRM semantics dictionary that the classifier can consult before or alongside the fallback heuristics.

## Goals / Non-Goals

**Goals:**
- Introduce a maintainable PRM semantics dictionary instead of adding more ad-hoc hardcoded rules.
- Enrich PRM classification output with `family`, `feature`, `instance`, `description`, and `tunable`.
- Keep existing `stage` and `category` fields available so current compare/import flows do not break.
- Use the new semantic fields in import-detail browsing so documented unmapped families become navigable.
- Implement a first-wave dictionary covering the highest-value documented families.

**Non-Goals:**
- Fully redesign the compare UI around the new semantic model in this change.
- Persist enriched semantic metadata in the database schema.
- Achieve exhaustive coverage for every remaining unmapped PRM parameter in one pass.

## Decisions

### 1. Add a dictionary data file rather than encode all rules in Python
The classifier will load rules from a checked-in structured file under the web layer. This keeps the taxonomy editable without forcing future contributors to rewrite classifier logic.

Alternatives considered:
- Continue expanding Python sets and keyword maps: rejected because the rule base is already outgrowing simple prefix buckets.
- Add a new database table: rejected for now because this semantic layer is static application knowledge, not imported recipe data.

### 2. Preserve `stage/category` and add richer fields
The API and UI will continue to receive `stage` and `category`, but PRM rows will also include `family`, `feature`, `instance`, `description`, and `tunable`.

Alternatives considered:
- Replace `stage/category` entirely: rejected because current import and compare views still depend on them.
- Only expose the richer fields in frontend code: rejected because the backend is the authoritative place to normalize semantics.

### 3. Dictionary rules should support regex captures for indexed families
Families like `SF10_Pullout_Dist` and `SL3_Scalar` need both a shared classification and the captured index (`sf10`, `sl3`). Regex-based rules with named groups cover this cleanly.

Alternatives considered:
- Enumerate every indexed parameter explicitly: rejected because it is repetitive and hard to maintain.
- Infer instance purely in frontend code: rejected because it duplicates parsing logic and would diverge from API semantics.

### 4. Import-detail browsing will use family/feature as the primary new facets
The first UI integration will be limited to import-detail PRM browsing. This keeps the scope aligned with the immediate need to organize unmapped parameters without reopening the compare overhaul.

Alternatives considered:
- Update compare and detail in the same change: rejected as too broad for a first integration step.

## Risks / Trade-offs

- [Dictionary incompleteness] -> Keep fallback heuristic classification and mark unknown values explicitly.
- [Frontend complexity grows with more facets] -> Limit first-wave UI changes to import detail and keep dependent filters client-side.
- [Rule ordering bugs] -> Evaluate dictionary rules before heuristic fallback and cover representative families with tests.
- [Semantic drift between memo and code] -> Store human-readable descriptions alongside rules so the codebase reflects the documented meaning.

## Migration Plan

1. Add the new PRM semantics dictionary file and loader.
2. Extend classifier output and import API row payloads with richer semantics.
3. Update import-detail types and PRM filter UI to use family/feature semantics.
4. Keep existing consumers compatible by retaining `stage/category`.
5. Expand coverage incrementally in later changes by editing the dictionary file.

## Open Questions

- Whether compare should eventually group by `family/feature` instead of only `stage/category`.
- Whether `_Conv` and other fixed compatibility flags should be hidden by default in the UI once `tunable = false` is available.
