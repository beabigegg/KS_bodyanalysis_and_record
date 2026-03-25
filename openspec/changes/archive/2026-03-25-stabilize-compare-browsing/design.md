## Context

The compare page currently posts one request and receives parameter diffs, APP diffs, BSG diffs, RPM limit diffs, and RPM reference diffs together. The frontend then constructs all section tables in one render pass. This is convenient for implementation but expensive for real recipe data, where parameter diffs alone can already be large.

The browser issue is primarily a rendering and payload-size problem. The backend still needs to compute diffs, but the client should not receive or render everything at once.

## Goals / Non-Goals

**Goals:**
- Limit compare payload size by requesting only one diff section at a time.
- Cap rendered rows by adding pagination at the API and UI layers.
- Preserve existing compare semantics for diff detection and classification.

**Non-Goals:**
- Rework recipe selection on the compare page.
- Introduce virtualization libraries.
- Change compare business rules for what counts as a diff.

## Decisions

### 1. Make compare requests section-specific

The compare request will accept a `section` field with values such as `params`, `app_spec`, `bsg`, `rpm_limits`, and `rpm_reference`. The response will include shared compare context (`imports`, `wire_group_context`) plus only the active section's rows.

This directly reduces payload size and avoids sending unused sections to the browser.

### 2. Add server-side pagination to compare responses

The compare request will also accept `page` and `page_size`, and the backend will slice the active section rows before returning them. This bounds DOM size and keeps the page usable even when a section still has many diffs.

### 3. Keep parameter-specific filters on the parameter section only

`file_type` filtering remains useful for `params` but not for APP/BSG/RPM sections. The UI will expose it only while the parameter section is active.

## Risks / Trade-offs

- Users lose the "everything visible at once" overview → Mitigation: keep section tabs visible and show each section's total for the loaded section.
- Backend still computes a full section before slicing → Mitigation: this is acceptable as the immediate stability issue is browser-side payload/render cost.
- API shape changes for compare → Mitigation: only the project frontend uses this route, and tests will lock in the new contract.
