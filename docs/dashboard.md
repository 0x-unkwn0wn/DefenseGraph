# Dashboard

The Dashboard is the main current-state landing page for DefenseGraph.

## KPI Definitions

- `Theoretical Coverage %` = techniques with `theoretical_effect != none` / total techniques
- `Real Coverage %` = techniques with `real_effect != none` / total techniques
- `Tested Coverage %` = techniques with `test_status != not_tested` / total techniques
- `Critical Gaps` = techniques with no real coverage, failed tests, or missing primary scope
- `Detect-Only Techniques` = techniques whose strongest real effect is detect only
- `Low Confidence Techniques` = techniques with real coverage but low confidence

## Sections

- Top Risks
- Coverage by Domain
- Coverage by Scope
- Validation / Tested Status
- Snapshot delta

The MVP dashboard is intentionally operational, not decorative. It reuses the live coverage engine output rather than a separate analytics model.
