# Confidence Model

DefenseGraph tracks confidence per `ToolCapability`.

## Fields

- `implementation_level`: `none`, `partial`, `full`
- `control_effect`: `detect`, `block`, `prevent`
- `confidence_source`: `declared`, `assessed`, `evidenced`, `tested`
- `confidence_level`: `low`, `medium`, `high`

## Source progression

- `declared`: the tool capability exists, but only as a manual declaration.
- `assessed`: the capability has questionnaire answers.
- `evidenced`: at least one manual evidence item is attached.
- `tested`: reserved for stronger validation paths and future BAS workflows.

Source precedence is:

`tested > evidenced > assessed > declared`

## Assessment scoring

Each answer contributes:

- `yes = 2`
- `partial = 1`
- `no = 0`
- `unknown = 0`

The score is normalized against `max_score = question_count * 2`.

Confidence level thresholds:

- `high` when score ratio is `>= 0.75`
- `medium` when score ratio is `>= 0.35` and `< 0.75`
- `low` otherwise

## Effective confidence logic

- Tool capability only: `declared + low`
- Questionnaire answered: `assessed + scored level`
- Evidence attached: `evidenced + max(scored level, medium)`
- Tested: reserved override to `tested + high`

This keeps the MVP simple while still separating implementation state from confidence state.
