# Coverage Rules

DefenseGraph derives ATT&CK coverage from assigned capabilities, tool type, dependencies, confidence, and now configuration status.

## 1. Base contribution model

Direct `control` tools can contribute:

- `detect`
- `block`
- `prevent`

`analytics` tools can contribute only:

- `detect`

and only when required data sources are present.

`response` tools do not contribute direct ATT&CK coverage by themselves.

They only enhance an existing detection path.

## 2. Configuration-dependent controls

If a capability has `requires_configuration = false`, coverage behaves as before.

If a capability has `requires_configuration = true`, DefenseGraph evaluates its configuration profile before using it in ATT&CK coverage.

### Unknown configuration

- capability may still appear as weak coverage
- confidence is capped at `low`
- technique gets `is_gap_unconfigured_control = true`

### Not enabled

- capability does not contribute effective coverage
- technique remains uncovered unless another tool contributes
- technique gets `is_gap_unconfigured_control = true`

### Partially enabled

- capability contributes only a partial path
- technique gets `is_gap_partially_configured_control = true`

### Enabled

- capability contributes normally

## 3. Confidence interaction

For configuration-dependent capabilities:

- no configuration profile -> confidence cannot exceed `low`
- `not_enabled` -> confidence stays `low`
- `partially_enabled` -> confidence remains constrained unless stronger evidence exists
- `enabled` -> confidence follows the normal declared / assessed / evidenced / tested model

## 4. Technique-level flags

Coverage now surfaces these additional gaps:

- `is_gap_unconfigured_control`
- `is_gap_partially_configured_control`

These are separate from:

- `is_gap_no_coverage`
- `is_gap_detect_only`
- `is_gap_partial`
- `is_gap_low_confidence`
- `is_gap_single_tool_dependency`
- `is_gap_missing_data_sources`
- `is_gap_detection_without_response`
- `is_gap_response_without_detection`

## 5. Practical interpretation

- installed tool != effective control
- selected capability != active protection
- verified configuration + confidence + dependencies = credible ATT&CK coverage
