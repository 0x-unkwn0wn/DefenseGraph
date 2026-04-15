## Mapping Model

`CapabilityTechniqueMap` is now treated as a structural relationship only.

### What the mapping means

A mapping row means:

- the capability is relevant to the ATT&CK technique
- the relationship exists for coverage and documentation purposes
- structural metadata such as `coverage` can still describe how direct or complete that relationship is

### What the mapping no longer means

The mapping does not decide runtime effect anymore.

It does not:

- cap a tool at `detect`
- force a tool down from `prevent` to `block`
- null out an override because the historical mapping used another effect

### Runtime behavior

Coverage contribution is allowed only when:

- the capability has a structural mapping to the technique

Once that structural relationship exists:

- `ToolCapability.control_effect_default` provides the default actual effect
- `ToolCapabilityTechniqueOverride.control_effect_override` is authoritative for that technique when present

### Legacy field

The database still contains `CapabilityTechniqueMap.control_effect` because it is part of the existing schema and seed data.

That field is now legacy metadata:

- preserved for compatibility and migration safety
- not used by the coverage engine
- not used to clip tool defaults or overrides
- not shown as authoritative runtime behavior in the UI
