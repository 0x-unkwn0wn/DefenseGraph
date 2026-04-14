# Coverage Dependencies

DefenseGraph now derives ATT&CK coverage from three tool classes:

- `control`
- `analytics`
- `response`

## Direct control tools

Control tools behave as before:

- they can contribute `detect`
- they can contribute `block`
- they can contribute `prevent`

Their best effect still drives the base ATT&CK outcome.

## Analytics dependencies

Analytics tools contribute only when capability dependencies are satisfied.

Capability metadata can declare:

- `requires_data_sources`
- `supported_by_analytics`
- `supported_by_response`

Capabilities can also list required or recommended data sources explicitly.

## Response dependencies

Response tools do not create direct coverage.

They only matter when:

- a technique already has upstream detection
- a linked response action exists for that technique path

When both conditions are true:

- `response_enabled = true`
- `effective_outcome = detect_with_response`

## Coverage result fields

For each technique, the API now returns:

- `effective_control_effect`
- `effective_outcome`
- `tool_count`
- `confidence_level`
- `coverage_status`
- `response_enabled`
- `dependency_flags`

## Dependency gap flags

The coverage engine also calculates:

- `is_gap_missing_data_sources`
- `is_gap_detection_without_response`
- `is_gap_response_without_detection`

## Interpretation

- `missing_data_sources`
  - analytics coverage was configured, but required telemetry is missing or incomplete

- `detection_without_response`
  - a technique is detected, but no linked response path exists

- `response_without_detection`
  - response actions exist, but there is no upstream detection to trigger them

This keeps the model simple while removing two common false assumptions:

- "We have a SIEM, so we must cover the technique"
- "We have SOAR, so we must already respond effectively"
