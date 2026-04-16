# Test Status Model

DefenseGraph supports optional technique-level testing without requiring a BAS integration.

## Test Status Values

- `not_tested`
- `passed`
- `partial`
- `failed`
- `detected_not_blocked`

## Storage Model

The current MVP reuses the existing validation table and exposes it through `/test-results` endpoints.

Each test result can include:

- technique
- optional linked tool
- test status
- date
- notes

## Aggregation

Technique coverage exposes:

- `test_results`: individual recorded validations
- `test_status`: strongest current status for the technique
- `test_status_summary`: counts by status

`failed` and `detected_not_blocked` are treated as explicit gap signals.
