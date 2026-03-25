## 1. Backend compare paging

- [x] 1.1 Change `web/routes/compare.py` to accept section and paging parameters
- [x] 1.2 Return only the active compare section rows plus paging metadata
- [x] 1.3 Keep existing parameter classification and wire-group context behavior intact

## 2. Frontend compare browsing

- [x] 2.1 Update compare types and API usage for section-based responses
- [x] 2.2 Refactor `ComparePage` to fetch only the active section and page
- [x] 2.3 Add section tabs and paging controls so the browser never renders the entire compare result set at once

## 3. Verification

- [x] 3.1 Update compare route tests for section-based paged responses
- [x] 3.2 Run targeted backend tests and frontend build verification
