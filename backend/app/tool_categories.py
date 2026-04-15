CANONICAL_TOOL_CATEGORIES = [
    "Endpoint Security (EDR / XDR)",
    "Identity & Access Security (IAM / Identity Protection)",
    "Privileged Access Management (PAM)",
    "Network Security (NGFW / IDS / IPS / NDR)",
    "Application & API Security (WAF / WAAP)",
    "SASE / SSE (SWG / ZTNA / CASB)",
    "Email Security",
    "Device & Network Access Control (NAC)",
    "Security Analytics & Detection (SIEM / UEBA)",
    "SOAR & Security Automation",
    "Vulnerability & Exposure Management (Vuln Mgmt / ASM / EASM)",
    "Cloud Workload Protection (CWPP / runtime)",
    "OT / IoT Security",
    "Deception Technologies",
    "Data Loss Prevention (DLP / DSPM / Data Classification)",
]


LEGACY_CATEGORY_ALIASES = {
    "EDR": "Endpoint Security (EDR / XDR)",
    "Identity": "Identity & Access Security (IAM / Identity Protection)",
    "PAM": "Privileged Access Management (PAM)",
    "DNS": "Network Security (NGFW / IDS / IPS / NDR)",
    "SASE": "SASE / SSE (SWG / ZTNA / CASB)",
    "Email": "Email Security",
    "Security Analytics": "Security Analytics & Detection (SIEM / UEBA)",
    "SOAR": "SOAR & Security Automation",
    "DLP": "Data Loss Prevention (DLP / DSPM / Data Classification)",
    # BAS is no longer a standalone category in the canonical catalog.
    # Keep a deterministic fallback for legacy BAS-tagged tools and templates.
    "BAS": "Security Analytics & Detection (SIEM / UEBA)",
}


TOOL_LABEL_CATEGORY_HINTS = {
    "NAC / Visibility Platform": "Device & Network Access Control (NAC)",
    "WAF / API Security": "Application & API Security (WAF / WAAP)",
    "UEM / MDM": "Endpoint Security (EDR / XDR)",
    "Vulnerability Assessment": "Vulnerability & Exposure Management (Vuln Mgmt / ASM / EASM)",
    "Information Protection": "Data Loss Prevention (DLP / DSPM / Data Classification)",
    "Encryption": "Data Loss Prevention (DLP / DSPM / Data Classification)",
    "DLP": "Data Loss Prevention (DLP / DSPM / Data Classification)",
    "Data Classification": "Data Loss Prevention (DLP / DSPM / Data Classification)",
    "AD Security Assessment": "Identity & Access Security (IAM / Identity Protection)",
    "Credential Exposure Monitoring": "Identity & Access Security (IAM / Identity Protection)",
    "Password Policy Enforcement": "Identity & Access Security (IAM / Identity Protection)",
    "Password Audit / Assessment": "Identity & Access Security (IAM / Identity Protection)",
    "IAM Administration / Automation": "Identity & Access Security (IAM / Identity Protection)",
    "Identity Threat Protection": "Identity & Access Security (IAM / Identity Protection)",
    "AD Audit / Monitoring": "Identity & Access Security (IAM / Identity Protection)",
    "MFA": "Identity & Access Security (IAM / Identity Protection)",
    "SIEM": "Security Analytics & Detection (SIEM / UEBA)",
}


def normalize_tool_category(category: str, tool_type_labels: list[str] | None = None) -> str:
    if category in CANONICAL_TOOL_CATEGORIES:
        return category

    if category in LEGACY_CATEGORY_ALIASES:
        return LEGACY_CATEGORY_ALIASES[category]

    if category == "Other" and tool_type_labels:
        for label in tool_type_labels:
            canonical = TOOL_LABEL_CATEGORY_HINTS.get(label)
            if canonical is not None:
                return canonical

    return category


def get_category_lookup_values(category: str) -> list[str]:
    canonical = normalize_tool_category(category)
    values = [canonical]

    for legacy, mapped in LEGACY_CATEGORY_ALIASES.items():
        if mapped == canonical and legacy not in values:
            values.append(legacy)

    return values
