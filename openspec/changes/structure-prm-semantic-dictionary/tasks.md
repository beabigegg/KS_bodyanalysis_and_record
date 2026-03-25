## 1. Semantic Dictionary

- [x] 1.1 Add a structured PRM semantic dictionary file for documented unmapped families and internal flags
- [x] 1.2 Implement dictionary loading and matching support in the PRM classifier
- [x] 1.3 Extend classifier output to include richer semantic fields while preserving stage/category compatibility

## 2. Backend Integration

- [x] 2.1 Return the enriched PRM semantic fields from import browsing rows
- [x] 2.2 Extend import parameter facet generation to include family and feature counts for PRM rows
- [x] 2.3 Add or update backend tests for dictionary-backed PRM semantic rows and facets

## 3. Import Detail Browsing

- [x] 3.1 Update frontend types and PRM filter state to support family and feature semantics
- [x] 3.2 Update import detail browsing to filter and group PRM rows by family/feature while preserving Seg grouping
- [x] 3.3 Verify the frontend build and targeted tests, then mark the change complete
