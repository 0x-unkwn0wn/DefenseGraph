## Effect Model

DefenseGraph now resolves ATT&CK control effect from the tool implementation layer, not from the capability-to-technique mapping layer.

### Current model

- `ToolCapability.control_effect_default` is the default actual effect for that tool and capability.
- `ToolCapabilityTechniqueOverride.control_effect_override` is an optional technique-specific actual effect.
- The effective effect for a technique is:
  1. override, when present
  2. otherwise the tool capability default

### Aggregation

If a capability is structurally mapped to a technique, the resolved tool effect is accepted as-is and aggregated with other contributing tools.

- `available_effects` is the distinct set of resolved tool effects
- `best_effect` uses `prevent > block > detect > none`
- per-effect counts come from the resolved tool effects
- gap logic uses the same resolved effects

### Old model

Previously, `CapabilityTechniqueMap.control_effect` acted like a ceiling:

- a `prevent` override could be clipped down to `detect`
- a `detect` override could become `none` if the mapping only had `prevent`

That behavior is deprecated. Runtime effect no longer comes from the mapping table.

### Why this is more accurate

- ATT&CK techniques do not own one fixed `detect`, `block`, or `prevent` value
- the same capability can behave differently by tool and by technique
- per-technique overrides now represent the real deployed behavior without duplicating capabilities
