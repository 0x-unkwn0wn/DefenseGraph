# Confidence Model

DefenseGraph now separates the claimed effect of a control from the confidence behind that claim.

## Confidence Sources

- `declared`: the capability and effect were assigned, but nothing else was validated.
- `assessed`: the guided assessment questionnaire was completed.
- `evidenced`: supporting evidence or configuration artefacts were attached.
- `validated`: internal checks indicate the control is enabled and not currently blocked by dependencies.
- `tested`: the technique was explicitly tested and the result was recorded.

## Confidence Levels

- `low`
- `medium`
- `high`

## How Confidence Is Used

- Confidence does not replace the effect.
- Confidence helps explain how credible the current `real_effect` is.
- Low-confidence coverage is still shown, but it is surfaced as a gap condition and in the dashboard.
