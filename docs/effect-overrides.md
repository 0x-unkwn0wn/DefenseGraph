## Effect Overrides

DefenseGraph now supports two layers of control effect behavior for a tool capability:

- `control_effect_default`: the baseline effect for the capability on that tool.
- per-technique override: an optional ATT&CK-specific effect that replaces the default for one technique.

This exists because one capability can map to multiple ATT&CK techniques, but the tool may not behave the same way for each one.

Example:

- Capability: `Data Exfiltration Protection`
- Tool: `DLP`
- Default effect: `block`
- Override: `T1041 -> detect`

Result:

- `T1041` uses `detect`
- other related techniques still use `block`

## Coverage Behavior

During ATT&CK coverage evaluation, DefenseGraph now resolves the effective effect for each technique like this:

1. Start with the tool capability default.
2. If an override exists for that technique, use the override instead.
3. Apply the existing capability-to-technique mapping constraints.
4. Aggregate all resulting tool contributions for the technique.

Coverage outputs now reflect the effective post-override result:

- `available_effects`
- `best_effect`
- `detection_count`
- `blocking_count`
- `prevention_count`
- contributing tools, including whether the effect came from a default or an override

## Gap Analysis

Gap logic also uses the effective post-override effect.

That means:

- detect-only coverage still produces a detect-only gap
- an override can downgrade a technique from `block` to `detect`
- the gap view will reflect that downgrade immediately

## Migration Behavior

Existing databases keep their previous behavior after migration:

- legacy `control_effect` values move to `control_effect_default`
- no technique overrides are created automatically

Until a user adds overrides, coverage behaves exactly as it did before.
