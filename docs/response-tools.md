# Response Tools

DefenseGraph treats SOAR and response orchestration products as `tool_type = response`.

## Principle

Response tooling does not detect adversary behavior by itself.

It only improves operational outcome when upstream detection already exists.

## What response tools can do

- attach response actions to a technique
- upgrade `detect` to `detect_with_response`
- show that containment or account response is available

## What response tools cannot do

- create ATT&CK coverage on their own
- claim `detect`, `block`, or `prevent` without upstream detection

## Seeded response actions

- `Isolate Host`
- `Disable Account`
- `Block IP`
- `Kill Process`
- `Disable Session / Token`
- `Create Ticket / Escalate`
- `Trigger Containment Playbook`

## Example

- XSOAR with `Disable Account`
- QRadar detects suspicious identity abuse

Result:

- coverage remains detection-led
- `response_enabled = true`
- effective outcome becomes `detect_with_response`

If XSOAR exists without an upstream detecting tool, DefenseGraph flags `response_without_detection`.
