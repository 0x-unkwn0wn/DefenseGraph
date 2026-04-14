# Gap Rules

DefenseGraph enriches ATT&CK coverage with explicit weak-point flags.

## Base coverage

Each technique still resolves to one effective control effect:

- `none`
- `detect`
- `block`
- `prevent`

Priority:

`prevent > block > detect > none`

## Technique confidence

Technique confidence is aggregated from the contributions that support the effective control effect.

- If no contribution exists, confidence defaults to `low`.
- If multiple contributions exist for the effective effect, the highest confidence level is used.

## Gap flags

For each technique, the API returns:

- `is_gap_no_coverage`
- `is_gap_detect_only`
- `is_gap_partial`
- `is_gap_low_confidence`
- `is_gap_single_tool_dependency`

## Flag rules

- `no_coverage`
  - no tool contributes any effect to the technique

- `detect_only`
  - the best effective effect is `detect`

- `partial`
  - coverage exists, but every contribution supporting the effective effect is still partial
  - partial means `implementation_level = partial` or the ATT&CK mapping itself is partial

- `low_confidence`
  - coverage exists, but aggregated confidence is still `low`

- `single_tool_dependency`
  - exactly one tool covers the technique

## Coverage status

The summary `coverage_status` is derived in this order:

1. `no_coverage`
2. `detect_only`
3. `partial`
4. `low_confidence`
5. `covered`

`single_tool_dependency` is intentionally kept as a separate flag so it can remain visible even when coverage is otherwise acceptable.
