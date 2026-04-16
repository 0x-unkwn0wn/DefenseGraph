# Theoretical vs Real Coverage

DefenseGraph now exposes two coverage layers for every ATT&CK technique.

## Theoretical Coverage

`theoretical_effect` is the best effect implied by:

- the tool
- the assigned capability
- the default effect
- any per-technique override

This is what should happen if the control behaves as configured in the model.

## Real Coverage

`real_effect` is the effect that remains after the engine applies:

- configuration state
- dependency checks
- scope coverage

Examples:

- theoretical `prevent`, real `none` when the control exists but is not enabled
- theoretical `block`, real `block` when the configuration and scope are present
- theoretical `detect`, real `detect` with low confidence when evidence is weak

## Tested Status

Testing does not hide the theoretical model.

Instead, it adds a third layer:

- what the model says should happen
- what the engine believes is currently real
- what has actually been tested
