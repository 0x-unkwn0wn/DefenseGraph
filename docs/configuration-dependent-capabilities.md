# Configuration-Dependent Capabilities

DefenseGraph now distinguishes three different states:

- tool exists
- capability is assigned
- capability is actually configured and effective

This is important for platforms such as WAFs, firewalls, DNS security, and DLP controls where a product can be present but not truly enforcing the control path.

## Capability metadata

Some capabilities now declare:

- `requires_configuration`
- `configuration_profile_type`

Examples:

- `Web Application Protection` -> `waf`
- `DNS C2 Control` -> `dns_security`
- `Network Segmentation Enforcement` -> `segmentation`
- `Data Exfiltration Protection` -> `dlp_web`
- `Email Exfiltration Control` -> `dlp_email`
- `Email Phishing Protection` -> `phishing_email`

## Configuration profile

When a capability requires verification, DefenseGraph can store a `ToolCapabilityConfigurationProfile` for the specific tool-capability pair.

It tracks:

- `configuration_status`
- `notes`
- `last_updated_at`

Status values:

- `unknown`
- `not_enabled`
- `partially_enabled`
- `enabled`

## Checklist scoring

Configuration status is derived from short vendor-neutral checklist answers:

- `yes = 2`
- `partial = 1`
- `no = 0`
- `unknown = 0`

Thresholds:

- `enabled` when ratio >= `0.75`
- `partially_enabled` when ratio >= `0.35`
- `not_enabled` when ratio < `0.35`
- `unknown` when there is no profile or no useful verification yet

## Why this matters

This removes a common false assumption:

- "Cloudflare exists, therefore WAF prevention is active"
- "Palo Alto exists, therefore segmentation is enforced"
- "F5 exists, therefore app protection is blocking exploits"

DefenseGraph now requires explicit configuration verification before those capabilities are treated as credible coverage.
