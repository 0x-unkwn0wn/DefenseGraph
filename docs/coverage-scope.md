# Coverage Scope

DefenseGraph models not only whether a defensive capability exists, but where it applies.

Installed tool != global coverage.

## Scope taxonomy

The product uses exactly these scopes:

- `endpoint_user_device`
- `server`
- `cloud_workload`
- `identity`
- `network`
- `email`
- `saas`
- `public_facing_app`

## How scope works

Each `ToolCapability` can have one or more `ToolCapabilityScope` assignments.

Each assignment stores:

- scope
- status: `none`, `partial`, or `full`
- optional notes

If a capability has no assigned scope, DefenseGraph treats it as unknown, not global.

## Technique relevance

ATT&CK techniques can declare relevant scopes through `TechniqueRelevantScope`.

Examples:

- `T1190` requires `public_facing_app` as a primary scope
- `T1041` spans endpoint, server, and cloud contexts
- `T1550` is primarily about `identity`

Primary scopes matter most. A technique is not treated as effectively covered unless at least one primary relevant scope is covered.

## Coverage impact

Scope changes ATT&CK coverage in these ways:

- no relevant scope covered: effective coverage is reduced to `none`
- some relevant scopes covered: the technique can remain covered, but with scope gaps
- primary scope covered but other relevant scopes missing: technique is marked partial
- no scope assigned on the tool capability: confidence remains weak and the technique surfaces a scope gap

## Gap flags

The coverage engine now returns:

- `scope_summary.full_scopes`
- `scope_summary.partial_scopes`
- `scope_summary.missing_scopes`
- `is_gap_scope_missing`
- `is_gap_scope_partial`

This lets the UI answer:

"Where am I covered?"

instead of only:

"Am I covered?"

## Practical examples

- A DLP capability assigned only to endpoints does not imply server exfiltration coverage.
- `T1190` is not considered covered unless `public_facing_app` scope exists.
- A capability with only partial server scope can contribute, but the technique remains a partial gap.
