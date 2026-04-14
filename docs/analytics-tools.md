# Analytics Tools

DefenseGraph treats SIEM and security analytics platforms as `tool_type = analytics`.

## Principle

Analytics tooling does not create credible ATT&CK coverage by itself.

Coverage only becomes valid when three things exist together:

- the tool is assigned a relevant detection capability
- the required data sources are ingested
- confidence is supported by assessment and tuning state

## What analytics tools can do

- contribute `detect`
- contribute lower-confidence or partial detection when dependencies are weak

## What analytics tools cannot do

- claim `block` or `prevent` directly
- claim detection coverage when required data sources are absent

## Data source dependency logic

If a capability declares required data sources:

- no required sources ingested: no effective coverage
- required sources only partial: degraded detection, lower confidence
- required sources fully ingested: normal detection contribution

Recommended data sources do not block coverage, but they reduce confidence when missing.

## Examples

- QRadar + `Identity Misuse Detection` + no `Active Directory Logs`
  - does not provide credible ATT&CK detection coverage

- QRadar + `Identity Misuse Detection` + full `Active Directory Logs`
  - can contribute `detect`

- Splunk + `DNS C2 Control` + partial `DNS Logs`
  - can contribute only degraded detection and should remain a visible weak point
