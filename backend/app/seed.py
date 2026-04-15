from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Capability,
    CapabilityAssessmentQuestion,
    CapabilityAssessmentTemplate,
    CapabilityCoverageRole,
    CapabilityConfigurationQuestion,
    CapabilityRequiredDataSource,
    CapabilitySupportedResponseAction,
    CapabilityTechniqueMap,
    CoverageRole,
    CoverageScope,
    DataSource,
    ResponseAction,
    Technique,
    TechniqueRelevantScope,
    Tool,
    ToolCapability,
    ToolCapabilityTemplate,
    Vendor,
)


CAPABILITIES = [
    {
        "code": "CAP-001",
        "name": "Script Execution Control",
        "domain": "endpoint",
        "description": "Monitors and constrains suspicious script and command execution on managed endpoints.",
    },
    {
        "code": "CAP-002",
        "name": "PowerShell Control",
        "domain": "endpoint",
        "description": "Adds visibility and response controls for malicious or risky PowerShell activity.",
    },
    {
        "code": "CAP-003",
        "name": "Credential Dumping Protection",
        "domain": "endpoint",
        "description": "Reduces the likelihood of credential dumping and improves detection of memory access abuse.",
    },
    {
        "code": "CAP-004",
        "name": "Email Phishing Protection",
        "domain": "email",
        "description": "Detects and prevents phishing through email link, attachment, and sender protections.",
        "requires_configuration": True,
        "configuration_profile_type": "phishing_email",
    },
    {
        "code": "CAP-005",
        "name": "Command and Control Monitoring",
        "domain": "network",
        "description": "Provides telemetry for command-and-control traffic patterns across managed environments.",
    },
    {
        "code": "CAP-006",
        "name": "DNS C2 Control",
        "domain": "network",
        "description": "Detects or blocks command-and-control activity over DNS channels.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "supported_by_response": True,
        "requires_configuration": True,
        "configuration_profile_type": "dns_security",
    },
    {
        "code": "CAP-007",
        "name": "Data Exfiltration Protection",
        "domain": "data",
        "description": "Monitors and controls outbound data movement across common exfiltration paths.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "supported_by_response": True,
        "requires_configuration": True,
        "configuration_profile_type": "dlp_web",
    },
    {
        "code": "CAP-008",
        "name": "Brute Force Detection",
        "domain": "identity",
        "description": "Detects repeated authentication attempts and related password attack patterns.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "supported_by_response": True,
    },
    {
        "code": "CAP-009",
        "name": "Identity Misuse Detection",
        "domain": "identity",
        "description": "Detects suspicious account activity that may indicate identity abuse or takeover.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "supported_by_response": True,
    },
    {
        "code": "CAP-010",
        "name": "Privileged Misuse Protection",
        "domain": "identity",
        "description": "Constrains risky privileged actions and reduces misuse of elevated access.",
    },
    {
        "code": "CAP-011",
        "name": "Token Misuse Detection",
        "domain": "identity",
        "description": "Identifies suspicious token use and suspicious authentication token handling.",
    },
    {
        "code": "CAP-012",
        "name": "Remote Services Protection",
        "domain": "endpoint",
        "description": "Monitors and restricts risky use of remote services for lateral movement.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "supported_by_response": True,
    },
    {
        "code": "CAP-013",
        "name": "Ransomware Protection",
        "domain": "endpoint",
        "description": "Detects or blocks ransomware execution and destructive encryption behaviors.",
    },
    {
        "code": "CAP-014",
        "name": "Valid Account Abuse Protection",
        "domain": "identity",
        "description": "Adds controls against attacker use of otherwise valid or compromised identities.",
    },
    {
        "code": "CAP-015",
        "name": "Identity Session Protection",
        "domain": "identity",
        "description": "Protects live authentication sessions and limits misuse of active identity context.",
    },
    {
        "code": "CAP-016",
        "name": "Endpoint Script Telemetry",
        "domain": "endpoint",
        "description": "Provides lower-friction telemetry for script execution where stronger controls are not deployed.",
    },
    {
        "code": "CAP-017",
        "name": "Web Exfiltration Control",
        "domain": "data",
        "description": "Detects and disrupts outbound data exfiltration over web services or browsers.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "requires_configuration": True,
        "configuration_profile_type": "dlp_web",
    },
    {
        "code": "CAP-018",
        "name": "Email Exfiltration Control",
        "domain": "email",
        "description": "Monitors or blocks data loss over email delivery channels.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "requires_configuration": True,
        "configuration_profile_type": "dlp_email",
    },
    {
        "code": "CAP-019",
        "name": "Network Beacon Analysis",
        "domain": "network",
        "description": "Detects repeated network beaconing and periodic outbound communication patterns.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
    {
        "code": "CAP-020",
        "name": "Endpoint Behavior Analytics",
        "domain": "endpoint",
        "description": "Applies endpoint analytics to suspicious behavior patterns that support ATT&CK coverage.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
    {
        "code": "CAP-021",
        "name": "Account Change Monitoring",
        "domain": "identity",
        "description": "Monitors risky account changes and suspicious directory object modifications.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
    {
        "code": "CAP-022",
        "name": "Group Membership Monitoring",
        "domain": "identity",
        "description": "Monitors privileged group changes and suspicious directory membership activity.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
    {
        "code": "CAP-023",
        "name": "Credential Hygiene Enforcement",
        "domain": "identity",
        "description": "Improves credential quality with policy enforcement and hygiene controls.",
    },
    {
        "code": "CAP-024",
        "name": "Weak Password Prevention",
        "domain": "identity",
        "description": "Prevents weak, breached, or policy-violating passwords from being used.",
    },
    {
        "code": "CAP-025",
        "name": "Public-Facing Service Protection",
        "domain": "network",
        "description": "Detects and constrains exploit and unauthorized access activity targeting internet-exposed services.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "requires_configuration": True,
        "configuration_profile_type": "firewall",
    },
    {
        "code": "CAP-026",
        "name": "Containment Automation",
        "domain": "response",
        "description": "Automates standardized containment playbooks once an upstream detection has fired.",
        "supported_by_response": True,
    },
    {
        "code": "CAP-027",
        "name": "Account Disable Automation",
        "domain": "response",
        "description": "Automates disabling risky or compromised accounts after analyst-approved detections.",
        "supported_by_response": True,
    },
    {
        "code": "CAP-028",
        "name": "Host Isolation Automation",
        "domain": "response",
        "description": "Automates host isolation and containment workflows from upstream detections.",
        "supported_by_response": True,
    },
    {
        "code": "CAP-029",
        "name": "Credential Abuse Detection",
        "domain": "identity",
        "description": "Correlates suspicious authentication artifacts that indicate alternate credential abuse.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "supported_by_response": True,
    },
    {
        "code": "CAP-030",
        "name": "Remote Access Abuse Detection",
        "domain": "identity",
        "description": "Detects suspicious remote access use that may indicate compromised external access paths.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "supported_by_response": True,
    },
    {
        "code": "CAP-031",
        "name": "Web Application Protection",
        "domain": "network",
        "description": "Protects public-facing applications with exploit, signature, and request inspection controls.",
        "requires_configuration": True,
        "configuration_profile_type": "waf",
    },
    {
        "code": "CAP-032",
        "name": "Network Segmentation Enforcement",
        "domain": "network",
        "description": "Restricts lateral movement by enforcing production segmentation and east-west traffic policy.",
        "requires_configuration": True,
        "configuration_profile_type": "segmentation",
    },
    {
        "code": "CAP-101",
        "name": "Asset Visibility",
        "domain": "network",
        "description": "Maintains accurate visibility over assets, connected devices, and their defensive state.",
    },
    {
        "code": "CAP-102",
        "name": "Access Control",
        "domain": "network",
        "description": "Enforces access decisions for users, devices, and network-connected assets.",
    },
    {
        "code": "CAP-103",
        "name": "Device Posture Assessment",
        "domain": "endpoint",
        "description": "Assesses device health, posture, and defensive readiness before granting access.",
    },
    {
        "code": "CAP-104",
        "name": "Data Loss Prevention",
        "domain": "data",
        "description": "Applies generic controls to detect, govern, and prevent unauthorized data movement.",
    },
    {
        "code": "CAP-105",
        "name": "Data Exfiltration Policy Enforcement",
        "domain": "data",
        "description": "Enforces explicit policy decisions to stop disallowed outbound data transfer paths.",
        "requires_configuration": True,
        "configuration_profile_type": "dlp_web",
    },
    {
        "code": "CAP-106",
        "name": "Sensitivity Labelling",
        "domain": "data",
        "description": "Assigns business sensitivity labels to data so downstream controls can act consistently.",
    },
    {
        "code": "CAP-107",
        "name": "Data Classification",
        "domain": "data",
        "description": "Classifies data content and context to support governance and protection decisions.",
    },
    {
        "code": "CAP-108",
        "name": "Encryption Enforcement",
        "domain": "data",
        "description": "Enforces encryption for protected data across storage, sharing, and transfer paths.",
    },
    {
        "code": "CAP-109",
        "name": "Rights Protection",
        "domain": "data",
        "description": "Restricts downstream use of protected content through rights and usage controls.",
    },
    {
        "code": "CAP-110",
        "name": "Layer 7 Filtering",
        "domain": "network",
        "description": "Inspects and filters application-layer requests and traffic for security enforcement.",
        "requires_configuration": True,
        "configuration_profile_type": "firewall",
    },
    {
        "code": "CAP-111",
        "name": "Device Compliance Enforcement",
        "domain": "endpoint",
        "description": "Enforces compliance conditions before devices can access protected resources.",
    },
    {
        "code": "CAP-112",
        "name": "Endpoint Policy Management",
        "domain": "endpoint",
        "description": "Applies and governs endpoint configuration policy at scale.",
    },
    {
        "code": "CAP-113",
        "name": "Configuration Hardening",
        "domain": "endpoint",
        "description": "Reduces attack surface by applying hardened baseline configurations.",
    },
    {
        "code": "CAP-114",
        "name": "Group Policy Enforcement",
        "domain": "identity",
        "description": "Applies and governs directory-backed configuration policy across managed systems.",
    },
    {
        "code": "CAP-115",
        "name": "AD Security Assessment",
        "domain": "identity",
        "description": "Assesses Active Directory configuration and exposure for security weaknesses.",
    },
    {
        "code": "CAP-116",
        "name": "AD Exposure Review",
        "domain": "identity",
        "description": "Reviews directory exposure paths, delegation risk, and identity attack surface.",
    },
    {
        "code": "CAP-117",
        "name": "Leaked Credential Monitoring",
        "domain": "identity",
        "description": "Monitors for externally exposed or breached credentials associated with the organization.",
    },
    {
        "code": "CAP-118",
        "name": "External Exposure Discovery",
        "domain": "identity",
        "description": "Discovers external identity and infrastructure exposure that increases attack opportunity.",
    },
    {
        "code": "CAP-119",
        "name": "Password Policy Enforcement",
        "domain": "identity",
        "description": "Enforces password policy quality, banned password use, and hygiene requirements.",
    },
    {
        "code": "CAP-120",
        "name": "Password Weakness Auditing",
        "domain": "identity",
        "description": "Audits the directory for weak, risky, or policy-violating password conditions.",
    },
    {
        "code": "CAP-121",
        "name": "Compromised Password Discovery",
        "domain": "identity",
        "description": "Detects password exposure or compromise patterns that require remediation.",
    },
    {
        "code": "CAP-122",
        "name": "Identity Lifecycle Automation",
        "domain": "identity",
        "description": "Automates account lifecycle administration and controlled identity workflows.",
    },
    {
        "code": "CAP-123",
        "name": "AD Administration Workflow",
        "domain": "identity",
        "description": "Automates repeatable administrative change workflows in Active Directory.",
    },
    {
        "code": "CAP-124",
        "name": "Privileged Access Management",
        "domain": "identity",
        "description": "Controls privileged access, elevation, and governance of sensitive administrative paths.",
    },
    {
        "code": "CAP-125",
        "name": "Secrets Protection",
        "domain": "identity",
        "description": "Protects privileged secrets, credentials, and sensitive authentication material.",
    },
    {
        "code": "CAP-126",
        "name": "MFA Enforcement",
        "domain": "identity",
        "description": "Requires multi-factor authentication on protected access paths and user journeys.",
    },
    {
        "code": "CAP-127",
        "name": "Strong Authentication",
        "domain": "identity",
        "description": "Raises assurance of authentication flows through stronger verification controls.",
    },
    {
        "code": "CAP-128",
        "name": "Identity Threat Detection",
        "domain": "identity",
        "description": "Detects identity-centric attack activity across authentication, accounts, and sessions.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
        "supported_by_response": True,
    },
    {
        "code": "CAP-129",
        "name": "Identity Risk Monitoring",
        "domain": "identity",
        "description": "Monitors identity risk indicators that may warrant containment or stronger controls.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
    {
        "code": "CAP-130",
        "name": "Vulnerability Scanning",
        "domain": "network",
        "description": "Assesses assets for exploitable vulnerabilities and security exposure.",
    },
    {
        "code": "CAP-131",
        "name": "Misconfiguration Assessment",
        "domain": "network",
        "description": "Assesses systems and services for insecure or risky configuration states.",
    },
    {
        "code": "CAP-132",
        "name": "AD Change Auditing",
        "domain": "identity",
        "description": "Audits directory changes that alter access, privilege, and security-relevant state.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
    {
        "code": "CAP-133",
        "name": "Identity Activity Monitoring",
        "domain": "identity",
        "description": "Monitors ongoing identity activity for behavioral and control anomalies.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
    {
        "code": "CAP-134",
        "name": "Security Event Correlation",
        "domain": "analytics",
        "description": "Correlates multiple security signals into higher-fidelity detection outcomes.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
    {
        "code": "CAP-135",
        "name": "Security Event Monitoring",
        "domain": "analytics",
        "description": "Monitors security telemetry continuously to surface actionable signals and alerts.",
        "requires_data_sources": True,
        "supported_by_analytics": True,
    },
]

VENDORS = [
    {"name": "Forescout"},
    {"name": "Proofpoint"},
    {"name": "Microsoft"},
    {"name": "F5"},
    {"name": "PingCastle"},
    {"name": "FireCompass"},
    {"name": "Specops"},
    {"name": "ManageEngine"},
    {"name": "CyberArk"},
    {"name": "Swivel"},
    {"name": "CrowdStrike"},
    {"name": "Tenable"},
    {"name": "IBM"},
]

COVERAGE_ROLES = [
    {"code": "prevent", "name": "Prevent", "description": "Stops or blocks attacker activity before it succeeds."},
    {"code": "harden", "name": "Harden", "description": "Reduces attack surface and weak default states."},
    {"code": "detect", "name": "Detect", "description": "Identifies suspicious or malicious behavior."},
    {"code": "alert", "name": "Alert", "description": "Raises actionable signals for responders and workflows."},
    {"code": "assess", "name": "Assess", "description": "Measures exposure, posture, or security state."},
    {"code": "audit", "name": "Audit", "description": "Records or reviews control-relevant changes and history."},
    {"code": "govern", "name": "Govern", "description": "Applies policy, classification, or oversight decisions."},
    {"code": "respond", "name": "Respond", "description": "Supports containment or operational follow-up."},
    {"code": "automate", "name": "Automate", "description": "Automates security administration or response workflows."},
]

DATA_SOURCES = [
    {"code": "DS-001", "name": "Active Directory Logs", "category": "identity", "description": "Directory and authentication events from domain controllers and identity services."},
    {"code": "DS-002", "name": "Endpoint Telemetry", "category": "endpoint", "description": "Process, script, sensor, and behavioral telemetry from managed endpoints."},
    {"code": "DS-003", "name": "DNS Logs", "category": "network", "description": "DNS query, resolution, and policy decision logs."},
    {"code": "DS-004", "name": "Network Traffic Logs", "category": "network", "description": "Flow, session, or network analytics data for east-west and outbound traffic."},
    {"code": "DS-005", "name": "Firewall Logs", "category": "network", "description": "Connection and enforcement logs from perimeter or internal firewalls."},
    {"code": "DS-006", "name": "Email Logs", "category": "email", "description": "Mail gateway, delivery, click, and attachment handling events."},
    {"code": "DS-007", "name": "SaaS Audit Logs", "category": "cloud", "description": "Administrative and user audit records from SaaS platforms."},
    {"code": "DS-008", "name": "Cloud Control Plane Logs", "category": "cloud", "description": "Cloud administrative activity and control plane changes."},
    {"code": "DS-009", "name": "VPN / Remote Access Logs", "category": "identity", "description": "Remote access, VPN, and external access session logs."},
    {"code": "DS-010", "name": "Proxy / Web Logs", "category": "network", "description": "Proxy, secure web gateway, and web access inspection logs."},
]

RESPONSE_ACTIONS = [
    {"code": "RA-001", "name": "Isolate Host", "description": "Isolates an endpoint or workload from the network."},
    {"code": "RA-002", "name": "Disable Account", "description": "Disables a user or service account involved in suspicious activity."},
    {"code": "RA-003", "name": "Block IP", "description": "Pushes an IP block to a supported enforcement point."},
    {"code": "RA-004", "name": "Kill Process", "description": "Terminates a suspicious process on a supported endpoint."},
    {"code": "RA-005", "name": "Disable Session / Token", "description": "Revokes a risky session or invalidates active tokens."},
    {"code": "RA-006", "name": "Create Ticket / Escalate", "description": "Creates an analyst workflow item for review and follow-up."},
    {"code": "RA-007", "name": "Trigger Containment Playbook", "description": "Starts a broader containment playbook across connected systems."},
]

COVERAGE_SCOPES = [
    {
        "code": "endpoint_user_device",
        "name": "Endpoint / User Device",
        "description": "Coverage that applies to user workstations, laptops, and managed endpoints.",
    },
    {
        "code": "server",
        "name": "Server",
        "description": "Coverage that applies to server systems and hosted infrastructure.",
    },
    {
        "code": "cloud_workload",
        "name": "Cloud Workload",
        "description": "Coverage that applies to cloud-hosted workloads and compute services.",
    },
    {
        "code": "identity",
        "name": "Identity",
        "description": "Coverage that applies to authentication, directory, and identity control planes.",
    },
    {
        "code": "network",
        "name": "Network",
        "description": "Coverage that applies at the network transport or enforcement layer.",
    },
    {
        "code": "email",
        "name": "Email",
        "description": "Coverage that applies to mail delivery, mailboxes, and email flows.",
    },
    {
        "code": "saas",
        "name": "SaaS",
        "description": "Coverage that applies to SaaS platforms and application tenants.",
    },
    {
        "code": "public_facing_app",
        "name": "Public-Facing Application",
        "description": "Coverage that applies to internet-exposed applications and application delivery paths.",
    },
]

CAPABILITY_COVERAGE_ROLE_ASSIGNMENTS = {
    "Asset Visibility": ["detect", "assess"],
    "Access Control": ["prevent", "govern"],
    "Device Posture Assessment": ["assess", "detect"],
    "Data Loss Prevention": ["prevent", "detect", "govern"],
    "Data Exfiltration Policy Enforcement": ["prevent", "govern"],
    "Sensitivity Labelling": ["govern", "prevent"],
    "Data Classification": ["govern"],
    "Encryption Enforcement": ["prevent", "govern"],
    "Rights Protection": ["prevent", "govern"],
    "Web Application Protection": ["prevent", "detect"],
    "Layer 7 Filtering": ["prevent", "detect"],
    "Device Compliance Enforcement": ["harden", "prevent", "govern"],
    "Endpoint Policy Management": ["harden", "govern"],
    "Configuration Hardening": ["harden", "prevent"],
    "Group Policy Enforcement": ["harden", "prevent", "govern"],
    "AD Security Assessment": ["assess", "audit"],
    "AD Exposure Review": ["assess", "audit"],
    "Leaked Credential Monitoring": ["detect", "alert", "assess"],
    "External Exposure Discovery": ["detect", "assess"],
    "Password Policy Enforcement": ["harden", "prevent"],
    "Password Weakness Auditing": ["assess", "audit"],
    "Compromised Password Discovery": ["detect", "assess"],
    "Identity Lifecycle Automation": ["automate", "govern"],
    "AD Administration Workflow": ["automate", "govern"],
    "Privileged Access Management": ["prevent", "harden", "govern"],
    "Secrets Protection": ["prevent", "govern"],
    "MFA Enforcement": ["prevent", "harden"],
    "Strong Authentication": ["prevent", "harden"],
    "Identity Threat Detection": ["detect", "alert", "prevent"],
    "Identity Risk Monitoring": ["detect", "alert"],
    "Vulnerability Scanning": ["assess", "audit"],
    "Misconfiguration Assessment": ["assess", "audit"],
    "AD Change Auditing": ["audit", "detect", "alert"],
    "Identity Activity Monitoring": ["detect", "alert", "audit"],
    "Security Event Correlation": ["detect", "alert"],
    "Security Event Monitoring": ["detect", "alert"],
}

TOOL_CAPABILITY_NORMALIZATION_RULES = [
    {
        "tool_name": "Forescout",
        "vendor_name": "Forescout",
        "category": "Other",
        "tool_types": ["control"],
        "tool_type_labels": ["NAC / Visibility Platform"],
        "capabilities": [
            ("Asset Visibility", "detect", "full"),
            ("Access Control", "prevent", "full"),
            ("Device Posture Assessment", "detect", "full"),
        ],
    },
    {
        "tool_name": "Proofpoint DLP",
        "vendor_name": "Proofpoint",
        "category": "DLP",
        "tool_types": ["control"],
        "tool_type_labels": ["DLP"],
        "capabilities": [
            ("Data Loss Prevention", "detect", "full"),
            ("Data Exfiltration Policy Enforcement", "prevent", "full"),
        ],
    },
    {
        "tool_name": "Purview Labelling",
        "vendor_name": "Microsoft",
        "category": "Other",
        "tool_types": ["control"],
        "tool_type_labels": ["Information Protection"],
        "capabilities": [
            ("Sensitivity Labelling", "prevent", "full"),
            ("Data Classification", "detect", "full"),
        ],
    },
    {
        "tool_name": "Purview Encryption",
        "vendor_name": "Microsoft",
        "category": "Other",
        "tool_types": ["control"],
        "tool_type_labels": ["Encryption"],
        "capabilities": [
            ("Encryption Enforcement", "prevent", "full"),
            ("Rights Protection", "prevent", "full"),
        ],
    },
    {
        "tool_name": "F5 BIG-IP WAF",
        "vendor_name": "F5",
        "category": "Other",
        "tool_types": ["control"],
        "tool_type_labels": ["WAF / API Security"],
        "capabilities": [
            ("Web Application Protection", "prevent", "full"),
            ("Layer 7 Filtering", "block", "full"),
        ],
    },
    {
        "tool_name": "MDM Intune",
        "vendor_name": "Microsoft",
        "category": "Other",
        "tool_types": ["control"],
        "tool_type_labels": ["UEM / MDM"],
        "capabilities": [
            ("Device Compliance Enforcement", "prevent", "full"),
            ("Endpoint Policy Management", "prevent", "full"),
        ],
    },
    {
        "tool_name": "Group Policy Manager",
        "vendor_name": "ManageEngine",
        "category": "Identity",
        "tool_types": ["control"],
        "tool_type_labels": ["Policy Enforcement / Hardening"],
        "capabilities": [
            ("Configuration Hardening", "prevent", "full"),
            ("Group Policy Enforcement", "prevent", "full"),
        ],
    },
    {
        "tool_name": "PingCastle",
        "vendor_name": "PingCastle",
        "category": "Identity",
        "tool_types": ["control"],
        "tool_type_labels": ["AD Security Assessment"],
        "capabilities": [
            ("AD Security Assessment", "detect", "full"),
            ("AD Exposure Review", "detect", "full"),
        ],
    },
    {
        "tool_name": "FireCompass Leaked Credentials",
        "vendor_name": "FireCompass",
        "category": "Identity",
        "tool_types": ["control"],
        "tool_type_labels": ["Credential Exposure Monitoring"],
        "capabilities": [
            ("Leaked Credential Monitoring", "detect", "full"),
            ("External Exposure Discovery", "detect", "full"),
        ],
    },
    {
        "tool_name": "Specops Password Policy",
        "vendor_name": "Specops",
        "category": "Identity",
        "tool_types": ["control"],
        "tool_type_labels": ["Password Policy Enforcement"],
        "capabilities": [
            ("Password Policy Enforcement", "prevent", "full"),
        ],
    },
    {
        "tool_name": "Specops Password Auditor",
        "vendor_name": "Specops",
        "category": "Identity",
        "tool_types": ["control"],
        "tool_type_labels": ["Password Audit / Assessment"],
        "capabilities": [
            ("Password Weakness Auditing", "detect", "full"),
            ("Compromised Password Discovery", "detect", "full"),
        ],
    },
    {
        "tool_name": "ADManager Plus",
        "vendor_name": "ManageEngine",
        "category": "Identity",
        "tool_types": ["control"],
        "tool_type_labels": ["IAM Administration / Automation"],
        "capabilities": [
            ("Identity Lifecycle Automation", "prevent", "full"),
            ("AD Administration Workflow", "prevent", "full"),
        ],
    },
    {
        "tool_name": "CyberArk",
        "vendor_name": "CyberArk",
        "category": "PAM",
        "tool_types": ["control"],
        "tool_type_labels": ["PAM"],
        "capabilities": [
            ("Privileged Access Management", "prevent", "full"),
            ("Secrets Protection", "prevent", "full"),
        ],
    },
    {
        "tool_name": "Swivel",
        "vendor_name": "Swivel",
        "category": "Identity",
        "tool_types": ["control"],
        "tool_type_labels": ["MFA"],
        "capabilities": [
            ("MFA Enforcement", "prevent", "full"),
            ("Strong Authentication", "prevent", "full"),
        ],
    },
    {
        "tool_name": "CrowdStrike Identity",
        "vendor_name": "CrowdStrike",
        "category": "Identity",
        "tool_types": ["control", "analytics"],
        "tool_type_labels": ["Identity Threat Protection"],
        "capabilities": [
            ("Identity Threat Detection", "detect", "full"),
            ("Identity Risk Monitoring", "detect", "full"),
        ],
    },
    {
        "tool_name": "Tenable / Nessus",
        "vendor_name": "Tenable",
        "category": "Other",
        "tool_types": ["control"],
        "tool_type_labels": ["Vulnerability Assessment"],
        "capabilities": [
            ("Vulnerability Scanning", "detect", "full"),
            ("Misconfiguration Assessment", "detect", "full"),
        ],
    },
    {
        "tool_name": "ADAudit Plus",
        "vendor_name": "ManageEngine",
        "category": "Identity",
        "tool_types": ["control", "analytics"],
        "tool_type_labels": ["AD Audit / Monitoring"],
        "capabilities": [
            ("AD Change Auditing", "detect", "full"),
            ("Identity Activity Monitoring", "detect", "full"),
        ],
    },
    {
        "tool_name": "QRadar",
        "vendor_name": "IBM",
        "category": "Security Analytics",
        "tool_types": ["analytics"],
        "tool_type_labels": ["SIEM"],
        "capabilities": [
            ("Security Event Correlation", "detect", "full"),
            ("Security Event Monitoring", "detect", "full"),
        ],
    },
]

CAPABILITY_REQUIRED_DATA_SOURCES = [
    ("CAP-003", "DS-002", "required"),
    ("CAP-004", "DS-006", "required"),
    ("CAP-005", "DS-004", "required"),
    ("CAP-006", "DS-003", "required"),
    ("CAP-007", "DS-004", "required"),
    ("CAP-007", "DS-010", "recommended"),
    ("CAP-008", "DS-001", "required"),
    ("CAP-008", "DS-009", "recommended"),
    ("CAP-009", "DS-001", "required"),
    ("CAP-009", "DS-002", "recommended"),
    ("CAP-009", "DS-009", "recommended"),
    ("CAP-012", "DS-009", "required"),
    ("CAP-012", "DS-002", "recommended"),
    ("CAP-012", "DS-005", "recommended"),
    ("CAP-017", "DS-010", "required"),
    ("CAP-018", "DS-006", "required"),
    ("CAP-019", "DS-004", "required"),
    ("CAP-019", "DS-003", "recommended"),
    ("CAP-020", "DS-002", "required"),
    ("CAP-021", "DS-001", "required"),
    ("CAP-022", "DS-001", "required"),
    ("CAP-025", "DS-005", "required"),
    ("CAP-025", "DS-010", "recommended"),
    ("CAP-029", "DS-001", "required"),
    ("CAP-029", "DS-009", "recommended"),
    ("CAP-030", "DS-009", "required"),
    ("CAP-030", "DS-005", "recommended"),
]

CAPABILITY_SUPPORTED_RESPONSE_ACTIONS = [
    ("CAP-003", "RA-001"),
    ("CAP-003", "RA-004"),
    ("CAP-003", "RA-007"),
    ("CAP-005", "RA-001"),
    ("CAP-005", "RA-003"),
    ("CAP-005", "RA-006"),
    ("CAP-006", "RA-003"),
    ("CAP-007", "RA-001"),
    ("CAP-007", "RA-006"),
    ("CAP-008", "RA-002"),
    ("CAP-008", "RA-006"),
    ("CAP-009", "RA-002"),
    ("CAP-009", "RA-005"),
    ("CAP-009", "RA-006"),
    ("CAP-010", "RA-002"),
    ("CAP-010", "RA-005"),
    ("CAP-012", "RA-001"),
    ("CAP-012", "RA-003"),
    ("CAP-012", "RA-006"),
    ("CAP-013", "RA-001"),
    ("CAP-013", "RA-004"),
    ("CAP-013", "RA-007"),
    ("CAP-029", "RA-002"),
    ("CAP-029", "RA-005"),
    ("CAP-030", "RA-002"),
    ("CAP-030", "RA-006"),
]

TECHNIQUE_RELEVANT_SCOPES = [
    ("T1566", "email", "primary"),
    ("T1566", "endpoint_user_device", "secondary"),
    ("T1190", "public_facing_app", "primary"),
    ("T1190", "server", "secondary"),
    ("T1133", "identity", "primary"),
    ("T1133", "public_facing_app", "secondary"),
    ("T1059", "endpoint_user_device", "primary"),
    ("T1059", "server", "primary"),
    ("T1059", "cloud_workload", "secondary"),
    ("T1059.001", "endpoint_user_device", "primary"),
    ("T1059.001", "server", "secondary"),
    ("T1059.003", "endpoint_user_device", "primary"),
    ("T1059.003", "server", "secondary"),
    ("T1204", "endpoint_user_device", "primary"),
    ("T1204", "email", "secondary"),
    ("T1204", "saas", "secondary"),
    ("T1547", "endpoint_user_device", "primary"),
    ("T1547", "server", "secondary"),
    ("T1055", "endpoint_user_device", "primary"),
    ("T1055", "server", "primary"),
    ("T1068", "endpoint_user_device", "primary"),
    ("T1068", "server", "primary"),
    ("T1068", "cloud_workload", "secondary"),
    ("T1136", "identity", "primary"),
    ("T1136", "server", "secondary"),
    ("T1136", "saas", "secondary"),
    ("T1098", "identity", "primary"),
    ("T1098", "saas", "secondary"),
    ("T1484", "identity", "primary"),
    ("T1484", "server", "secondary"),
    ("T1003", "endpoint_user_device", "primary"),
    ("T1003", "server", "primary"),
    ("T1003.006", "identity", "primary"),
    ("T1003.006", "server", "secondary"),
    ("T1110", "identity", "primary"),
    ("T1110", "public_facing_app", "secondary"),
    ("T1550", "identity", "primary"),
    ("T1550", "endpoint_user_device", "secondary"),
    ("T1558", "identity", "primary"),
    ("T1558", "server", "secondary"),
    ("T1087", "identity", "primary"),
    ("T1087", "endpoint_user_device", "secondary"),
    ("T1087", "server", "secondary"),
    ("T1082", "endpoint_user_device", "primary"),
    ("T1082", "server", "secondary"),
    ("T1082", "cloud_workload", "secondary"),
    ("T1016", "endpoint_user_device", "primary"),
    ("T1016", "server", "primary"),
    ("T1016", "cloud_workload", "secondary"),
    ("T1016", "network", "secondary"),
    ("T1135", "server", "primary"),
    ("T1135", "endpoint_user_device", "secondary"),
    ("T1021", "server", "primary"),
    ("T1021", "endpoint_user_device", "secondary"),
    ("T1078", "identity", "primary"),
    ("T1078", "endpoint_user_device", "secondary"),
    ("T1078", "saas", "secondary"),
    ("T1570", "endpoint_user_device", "primary"),
    ("T1570", "server", "primary"),
    ("T1071", "endpoint_user_device", "primary"),
    ("T1071", "server", "primary"),
    ("T1071", "cloud_workload", "secondary"),
    ("T1071.004", "endpoint_user_device", "primary"),
    ("T1071.004", "server", "primary"),
    ("T1071.004", "network", "secondary"),
    ("T1568", "endpoint_user_device", "primary"),
    ("T1568", "server", "secondary"),
    ("T1568", "public_facing_app", "secondary"),
    ("T1090", "network", "primary"),
    ("T1090", "endpoint_user_device", "secondary"),
    ("T1090", "server", "secondary"),
    ("T1105", "endpoint_user_device", "primary"),
    ("T1105", "server", "primary"),
    ("T1105", "cloud_workload", "secondary"),
    ("T1114", "email", "primary"),
    ("T1114", "saas", "secondary"),
    ("T1041", "endpoint_user_device", "primary"),
    ("T1041", "server", "primary"),
    ("T1041", "cloud_workload", "secondary"),
    ("T1567", "saas", "primary"),
    ("T1567", "endpoint_user_device", "secondary"),
    ("T1567", "cloud_workload", "secondary"),
    ("T1537", "email", "primary"),
    ("T1537", "endpoint_user_device", "secondary"),
    ("T1486", "endpoint_user_device", "primary"),
    ("T1486", "server", "primary"),
    ("T1486", "cloud_workload", "secondary"),
]

ATTACK_TECHNIQUE_CATALOG = [
    {"code": "T1566", "name": "Phishing", "tactic": "Initial Access"},
    {"code": "T1190", "name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
    {"code": "T1133", "name": "External Remote Services", "tactic": "Initial Access"},
    {"code": "T1059", "name": "Command and Scripting Interpreter", "tactic": "Execution"},
    {"code": "T1059.001", "name": "PowerShell", "tactic": "Execution"},
    {"code": "T1059.003", "name": "Windows Command Shell", "tactic": "Execution"},
    {"code": "T1204", "name": "User Execution", "tactic": "Execution"},
    {
        "code": "T1547",
        "name": "Boot or Logon Autostart Execution",
        "tactic": "Persistence / Privilege Escalation / Defense Evasion",
    },
    {
        "code": "T1055",
        "name": "Process Injection",
        "tactic": "Persistence / Privilege Escalation / Defense Evasion",
    },
    {
        "code": "T1068",
        "name": "Exploitation for Privilege Escalation",
        "tactic": "Persistence / Privilege Escalation / Defense Evasion",
    },
    {
        "code": "T1136",
        "name": "Create Account",
        "tactic": "Persistence / Privilege Escalation / Defense Evasion",
    },
    {
        "code": "T1098",
        "name": "Account Manipulation",
        "tactic": "Persistence / Privilege Escalation / Defense Evasion",
    },
    {
        "code": "T1484",
        "name": "Domain or Group Policy Modification",
        "tactic": "Persistence / Privilege Escalation / Defense Evasion",
    },
    {"code": "T1003", "name": "OS Credential Dumping", "tactic": "Credential Access"},
    {"code": "T1003.006", "name": "DCSync", "tactic": "Credential Access"},
    {"code": "T1110", "name": "Brute Force", "tactic": "Credential Access"},
    {"code": "T1550", "name": "Use Alternate Authentication Material", "tactic": "Credential Access"},
    {"code": "T1558", "name": "Steal or Forge Kerberos Tickets", "tactic": "Credential Access"},
    {"code": "T1087", "name": "Account Discovery", "tactic": "Discovery"},
    {"code": "T1082", "name": "System Information Discovery", "tactic": "Discovery"},
    {"code": "T1016", "name": "System Network Configuration Discovery", "tactic": "Discovery"},
    {"code": "T1135", "name": "Network Share Discovery", "tactic": "Discovery"},
    {"code": "T1021", "name": "Remote Services", "tactic": "Lateral Movement"},
    {"code": "T1078", "name": "Valid Accounts", "tactic": "Lateral Movement"},
    {"code": "T1570", "name": "Lateral Tool Transfer", "tactic": "Lateral Movement"},
    {"code": "T1071", "name": "Application Layer Protocol", "tactic": "Command & Control"},
    {"code": "T1071.004", "name": "DNS", "tactic": "Command & Control"},
    {"code": "T1568", "name": "Dynamic Resolution", "tactic": "Command & Control"},
    {"code": "T1090", "name": "Proxy", "tactic": "Command & Control"},
    {"code": "T1105", "name": "Ingress Tool Transfer", "tactic": "Command & Control"},
    {"code": "T1114", "name": "Email Collection", "tactic": "Collection / Exfiltration"},
    {"code": "T1041", "name": "Exfiltration Over C2 Channel", "tactic": "Collection / Exfiltration"},
    {"code": "T1567", "name": "Exfiltration Over Web Service", "tactic": "Collection / Exfiltration"},
    {"code": "T1537", "name": "Exfiltration via Email", "tactic": "Collection / Exfiltration"},
    {"code": "T1486", "name": "Data Encrypted for Impact", "tactic": "Impact"},
]

CORE_TECHNIQUE_CODES = [
    "T1566",
    "T1133",
    "T1059",
    "T1059.001",
    "T1204",
    "T1003",
    "T1110",
    "T1550",
    "T1558",
    "T1021",
    "T1078",
    "T1071",
    "T1071.004",
    "T1568",
    "T1041",
    "T1567",
    "T1537",
    "T1486",
    "T1087",
    "T1547",
]

EXTENDED_TECHNIQUE_CODES = [
    "T1190",
    "T1059.003",
    "T1055",
    "T1068",
    "T1136",
    "T1098",
    "T1484",
    "T1003.006",
    "T1082",
    "T1016",
    "T1135",
    "T1570",
    "T1090",
    "T1105",
    "T1114",
]

TECHNIQUES = [
    {"code": technique["code"], "name": technique["name"]}
    for technique in ATTACK_TECHNIQUE_CATALOG
]

CAPABILITY_TECHNIQUE_MAPS = [
    ("CAP-001", "T1059", "detect", "full"),
    ("CAP-001", "T1059", "block", "full"),
    ("CAP-001", "T1059.003", "detect", "full"),
    ("CAP-001", "T1059.003", "block", "partial"),
    ("CAP-001", "T1204", "detect", "partial"),
    ("CAP-001", "T1055", "detect", "partial"),
    ("CAP-001", "T1547", "detect", "partial"),
    ("CAP-002", "T1059.001", "detect", "full"),
    ("CAP-002", "T1059.001", "block", "full"),
    ("CAP-003", "T1003", "detect", "full"),
    ("CAP-003", "T1003", "block", "full"),
    ("CAP-003", "T1003.006", "detect", "partial"),
    ("CAP-003", "T1003.006", "block", "partial"),
    ("CAP-004", "T1566", "detect", "full"),
    ("CAP-004", "T1566", "prevent", "full"),
    ("CAP-004", "T1204", "detect", "full"),
    ("CAP-004", "T1204", "prevent", "full"),
    ("CAP-005", "T1071", "detect", "full"),
    ("CAP-005", "T1568", "detect", "partial"),
    ("CAP-005", "T1090", "detect", "partial"),
    ("CAP-006", "T1071.004", "detect", "full"),
    ("CAP-006", "T1071.004", "block", "full"),
    ("CAP-006", "T1568", "detect", "full"),
    ("CAP-006", "T1568", "block", "partial"),
    ("CAP-007", "T1041", "detect", "full"),
    ("CAP-007", "T1041", "block", "full"),
    ("CAP-007", "T1114", "detect", "partial"),
    ("CAP-008", "T1110", "detect", "full"),
    ("CAP-008", "T1110", "block", "partial"),
    ("CAP-009", "T1078", "detect", "full"),
    ("CAP-009", "T1558", "detect", "partial"),
    ("CAP-009", "T1087", "detect", "partial"),
    ("CAP-009", "T1003.006", "detect", "partial"),
    ("CAP-010", "T1078", "prevent", "partial"),
    ("CAP-010", "T1550", "prevent", "full"),
    ("CAP-010", "T1558", "prevent", "partial"),
    ("CAP-010", "T1098", "prevent", "partial"),
    ("CAP-010", "T1484", "prevent", "partial"),
    ("CAP-011", "T1550", "detect", "full"),
    ("CAP-011", "T1558", "detect", "partial"),
    ("CAP-012", "T1133", "detect", "full"),
    ("CAP-012", "T1133", "block", "partial"),
    ("CAP-012", "T1021", "detect", "full"),
    ("CAP-012", "T1021", "block", "partial"),
    ("CAP-012", "T1570", "detect", "partial"),
    ("CAP-012", "T1135", "detect", "partial"),
    ("CAP-013", "T1486", "detect", "full"),
    ("CAP-013", "T1486", "block", "full"),
    ("CAP-014", "T1078", "detect", "partial"),
    ("CAP-014", "T1078", "block", "partial"),
    ("CAP-015", "T1550", "detect", "partial"),
    ("CAP-015", "T1550", "prevent", "partial"),
    ("CAP-015", "T1558", "prevent", "partial"),
    ("CAP-016", "T1204", "detect", "partial"),
    ("CAP-016", "T1059", "detect", "partial"),
    ("CAP-016", "T1059.001", "detect", "partial"),
    ("CAP-016", "T1059.003", "detect", "partial"),
    ("CAP-017", "T1567", "detect", "full"),
    ("CAP-017", "T1567", "block", "partial"),
    ("CAP-018", "T1537", "detect", "full"),
    ("CAP-018", "T1537", "prevent", "partial"),
    ("CAP-018", "T1114", "detect", "partial"),
    ("CAP-019", "T1071", "detect", "partial"),
    ("CAP-019", "T1071.004", "detect", "partial"),
    ("CAP-019", "T1568", "detect", "partial"),
    ("CAP-019", "T1090", "detect", "partial"),
    ("CAP-020", "T1055", "detect", "partial"),
    ("CAP-020", "T1547", "detect", "partial"),
    ("CAP-020", "T1068", "detect", "partial"),
    ("CAP-020", "T1082", "detect", "partial"),
    ("CAP-020", "T1016", "detect", "partial"),
    ("CAP-020", "T1486", "detect", "partial"),
    ("CAP-020", "T1021", "detect", "partial"),
    ("CAP-021", "T1078", "detect", "partial"),
    ("CAP-021", "T1087", "detect", "partial"),
    ("CAP-021", "T1136", "detect", "partial"),
    ("CAP-021", "T1098", "detect", "partial"),
    ("CAP-021", "T1484", "detect", "partial"),
    ("CAP-022", "T1078", "detect", "partial"),
    ("CAP-022", "T1087", "detect", "partial"),
    ("CAP-022", "T1484", "detect", "partial"),
    ("CAP-023", "T1110", "prevent", "partial"),
    ("CAP-024", "T1110", "prevent", "full"),
    ("CAP-025", "T1190", "detect", "full"),
    ("CAP-025", "T1190", "block", "partial"),
    ("CAP-025", "T1133", "detect", "partial"),
    ("CAP-025", "T1133", "block", "partial"),
    ("CAP-027", "T1078", "block", "full"),
    ("CAP-027", "T1136", "block", "partial"),
    ("CAP-027", "T1098", "block", "full"),
    ("CAP-027", "T1110", "block", "full"),
    ("CAP-027", "T1003", "block", "partial"),
    ("CAP-028", "T1021", "block", "full"),
    ("CAP-028", "T1105", "block", "partial"),
    ("CAP-028", "T1071", "block", "partial"),
    ("CAP-028", "T1041", "block", "full"),
    ("CAP-028", "T1570", "block", "full"),
    ("CAP-030", "T1078", "detect", "full"),
    ("CAP-030", "T1021", "detect", "full"),
    ("CAP-030", "T1133", "detect", "full"),
    ("CAP-030", "T1087", "detect", "partial"),
    ("CAP-030", "T1110", "detect", "partial"),
    ("CAP-031", "T1190", "detect", "full"),
    ("CAP-031", "T1190", "prevent", "full"),
    ("CAP-032", "T1021", "block", "full"),
    ("CAP-032", "T1021", "prevent", "partial"),
    ("CAP-032", "T1570", "block", "partial"),
    ("CAP-032", "T1135", "block", "partial"),
]

CAPABILITY_MAPPING_PATCHES_BY_NAME = {
    "Remote Access Abuse Detection": [
        ("T1078", "detect", "full"),
        ("T1021", "detect", "full"),
        ("T1133", "detect", "full"),
        ("T1087", "detect", "partial"),
        ("T1110", "detect", "partial"),
    ],
    "Host Isolation Automation": [
        ("T1021", "block", "full"),
        ("T1105", "block", "partial"),
        ("T1071", "block", "partial"),
        ("T1041", "block", "full"),
        ("T1570", "block", "full"),
    ],
    "Account Disable Automation": [
        ("T1078", "block", "full"),
        ("T1136", "block", "partial"),
        ("T1098", "block", "full"),
        ("T1110", "block", "full"),
        ("T1003", "block", "partial"),
    ],
}


def validate_attack_catalog(
    attack_catalog: Sequence[dict[str, str]] | None = None,
    core_codes: Sequence[str] | None = None,
    extended_codes: Sequence[str] | None = None,
    capability_maps: Sequence[tuple[str, str, str, str]] | None = None,
) -> None:
    catalog = list(attack_catalog or ATTACK_TECHNIQUE_CATALOG)
    core = list(core_codes or CORE_TECHNIQUE_CODES)
    extended = list(extended_codes or EXTENDED_TECHNIQUE_CODES)
    mappings = list(capability_maps or CAPABILITY_TECHNIQUE_MAPS)

    catalog_codes = [technique["code"] for technique in catalog]
    duplicate_codes = sorted({code for code in catalog_codes if catalog_codes.count(code) > 1})
    if duplicate_codes:
        raise ValueError(f"Duplicate ATT&CK technique IDs: {', '.join(duplicate_codes)}")

    missing_tactic = sorted(
        technique["code"]
        for technique in catalog
        if not technique.get("tactic")
    )
    if missing_tactic:
        raise ValueError(f"Techniques missing tactic assignments: {', '.join(missing_tactic)}")

    core_set = set(core)
    extended_set = set(extended)
    if len(core) != 20 or len(core_set) != 20:
        raise ValueError("Core technique set must contain exactly 20 unique techniques.")
    if len(extended) != 15 or len(extended_set) != 15:
        raise ValueError("Extended technique set must contain exactly 15 unique techniques.")

    overlap = sorted(core_set & extended_set)
    if overlap:
        raise ValueError(f"Techniques cannot appear in both Core and Extended: {', '.join(overlap)}")

    catalog_set = set(catalog_codes)
    if len(catalog_set) != 35:
        raise ValueError("ATT&CK catalog must contain exactly 35 unique techniques.")
    if core_set | extended_set != catalog_set:
        raise ValueError("Core and Extended technique sets must partition the 35-technique catalog exactly.")

    mapped_codes = {technique_code for _, technique_code, _, _ in mappings}
    unmapped = sorted(catalog_set - mapped_codes)
    if unmapped:
        raise ValueError(f"Techniques missing capability mappings: {', '.join(unmapped)}")


validate_attack_catalog()

CAPABILITY_ASSESSMENT_TEMPLATES = {
    "CAP-004": {
        "description": "Email phishing assessment checks whether common prevention and inspection controls are consistently enforced.",
        "questions": [
            "Is URL rewriting enabled for inbound email links?",
            "Are malicious attachments sandboxed before delivery?",
            "Are suspicious senders quarantined automatically?",
            "Is phishing reporting routed into an analyst workflow?",
        ],
    },
    "CAP-006": {
        "description": "DNS C2 assessment checks enforcement coverage, logging quality, and blocking behavior for managed endpoints.",
        "questions": [
            "Is DNS filtering enforced for all managed endpoints?",
            "Are high-risk DNS domains blocked automatically?",
            "Is DNS query logging retained for investigations?",
            "Are unmanaged or roaming endpoints covered by the same DNS policy?",
        ],
    },
    "CAP-003": {
        "description": "Credential dumping assessment checks hardening and telemetry around sensitive credential stores and memory access.",
        "questions": [
            "Is LSASS access protection enabled on supported endpoints?",
            "Are suspicious memory access attempts monitored?",
            "Are known credential dumping tools blocked or isolated automatically?",
            "Is tamper protection enabled for the relevant endpoint controls?",
        ],
    },
    "CAP-007": {
        "description": "Data exfiltration assessment checks whether outbound inspection and enforcement are applied consistently.",
        "questions": [
            "Is outbound data inspection active for email or web channels?",
            "Are sensitive data patterns enforced for blocking or quarantine?",
            "Are user or device exceptions reviewed regularly?",
            "Are alerts for unusual outbound transfer volumes triaged?",
        ],
    },
    "CAP-001": {
        "description": "Script execution assessment checks visibility and policy enforcement for generic script execution.",
        "questions": [
            "Is suspicious script execution monitored on managed endpoints?",
            "Are script control policies enforced for high-risk interpreters?",
            "Are execution alerts correlated with user or host context?",
            "Are script allowlists or restrictions reviewed regularly?",
        ],
    },
    "CAP-013": {
        "description": "Ransomware assessment checks prevention, isolation, and recovery-focused controls against encryption activity.",
        "questions": [
            "Are suspicious encryption behaviors detected automatically?",
            "Can affected endpoints be isolated quickly from the management console?",
            "Are ransomware-related process behaviors blocked automatically?",
            "Are recovery or rollback controls enabled where available?",
        ],
    },
    "CAP-009": {
        "description": "Identity misuse assessment checks anomaly detection and response coverage for suspicious sign-in behavior.",
        "questions": [
            "Are impossible travel or unusual sign-in patterns monitored?",
            "Are suspicious authentication alerts investigated promptly?",
            "Are risky sign-ins tied to adaptive enforcement decisions?",
            "Is identity telemetry correlated with endpoint or network context?",
        ],
    },
    "CAP-008": {
        "description": "Brute force assessment checks detection, rate limiting, and enforcement around repeated authentication attempts.",
        "questions": [
            "Are repeated failed sign-ins monitored centrally?",
            "Are lockout or throttling controls enforced for protected identities?",
            "Are authentication attack alerts reviewed by analysts?",
            "Is brute force coverage consistent across remote access entry points?",
        ],
    },
}

CAPABILITY_CONFIGURATION_QUESTIONS = {
    "CAP-031": {
        "profile_type": "waf",
        "questions": [
            "Is the WAF module enabled?",
            "Are blocking rules active, not just alerting?",
            "Are signatures or managed rules updated regularly?",
            "Is protection applied to all public-facing applications?",
        ],
    },
    "CAP-006": {
        "profile_type": "dns_security",
        "questions": [
            "Is DNS filtering enabled?",
            "Is blocking active, not only logging?",
            "Does it apply to all managed endpoints?",
        ],
    },
    "CAP-032": {
        "profile_type": "segmentation",
        "questions": [
            "Are segmentation policies enforced?",
            "Are east-west flows restricted?",
            "Are rules applied in production or only defined?",
        ],
    },
    "CAP-007": {
        "profile_type": "dlp_web",
        "questions": [
            "Are DLP policies enabled?",
            "Are policies enforced or alert-only?",
            "Is coverage tenant-wide?",
        ],
    },
    "CAP-017": {
        "profile_type": "dlp_web",
        "questions": [
            "Are web DLP policies enabled?",
            "Are web exfiltration policies enforced or alert-only?",
            "Is web inspection applied across managed traffic paths?",
        ],
    },
    "CAP-018": {
        "profile_type": "dlp_email",
        "questions": [
            "Are email DLP policies enabled?",
            "Are email policies enforced or alert-only?",
            "Is outbound email inspection active for the covered tenant?",
        ],
    },
    "CAP-004": {
        "profile_type": "phishing_email",
        "questions": [
            "Is inbound phishing protection enabled?",
            "Are malicious messages quarantined or blocked automatically?",
            "Are protections applied tenant-wide?",
        ],
    },
    "CAP-025": {
        "profile_type": "firewall",
        "questions": [
            "Are internet-facing protection policies enabled?",
            "Are protections enforced in production, not monitor-only?",
            "Do the policies cover all exposed services?",
        ],
    },
}

TOOL_TAGS = [
    {"name": "Active Directory", "default_categories": ["Identity", "PAM"]},
    {"name": "Authentication", "default_categories": ["Identity", "PAM", "SASE"]},
    {"name": "Privileged Access", "default_categories": ["PAM", "Identity"]},
    {"name": "Credential Hygiene", "default_categories": ["Identity"]},
    {"name": "Password Security", "default_categories": ["Identity"]},
    {"name": "DNS", "default_categories": ["DNS", "SASE"]},
    {"name": "Network Traffic", "default_categories": ["SASE", "DNS"]},
    {"name": "Segmentation", "default_categories": ["SASE"]},
    {"name": "Data Loss Prevention", "default_categories": ["DLP", "SASE"]},
    {"name": "Exfiltration Control", "default_categories": ["DLP", "SASE"]},
    {"name": "Email Security", "default_categories": ["Email"]},
    {"name": "Phishing", "default_categories": ["Email"]},
    {"name": "Endpoint Protection", "default_categories": ["EDR"]},
    {"name": "Process Monitoring", "default_categories": ["EDR"]},
    {"name": "Monitoring", "default_categories": ["EDR", "Identity", "DNS", "Email", "SASE"]},
    {"name": "Policy Enforcement", "default_categories": ["Identity", "DLP", "SASE", "Email"]},
    {"name": "Log Analytics", "default_categories": ["Security Analytics"]},
    {"name": "Correlation", "default_categories": ["Security Analytics"]},
    {"name": "Incident Response", "default_categories": ["SOAR"]},
    {"name": "Orchestration", "default_categories": ["SOAR"]},
]

CATEGORY_DEFAULT_TAGS = {
    "EDR": ["Endpoint Protection", "Process Monitoring", "Monitoring"],
    "PAM": ["Privileged Access", "Authentication", "Policy Enforcement"],
    "DLP": ["Data Loss Prevention", "Exfiltration Control", "Policy Enforcement"],
    "SASE": ["Network Traffic", "Segmentation", "Identity"],
    "DNS": ["DNS", "Network Traffic", "Monitoring"],
    "Email": ["Email Security", "Phishing", "Policy Enforcement"],
    "BAS": ["Monitoring"],
    "Identity": ["Authentication", "Credential Hygiene", "Policy Enforcement"],
    "Security Analytics": ["Log Analytics", "Correlation", "Monitoring"],
    "SOAR": ["Incident Response", "Orchestration", "Policy Enforcement"],
    "Other": [],
}

TOOL_CAPABILITY_TEMPLATES = [
    {
        "category": "EDR",
        "capability_code": "CAP-001",
        "optional_tags": ["Endpoint Protection", "Process Monitoring"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Common baseline for endpoint execution visibility.",
    },
    {
        "category": "EDR",
        "capability_code": "CAP-003",
        "optional_tags": ["Endpoint Protection", "Process Monitoring"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Typical EDR coverage for credential dumping activity.",
    },
    {
        "category": "EDR",
        "capability_code": "CAP-013",
        "optional_tags": ["Endpoint Protection"],
        "priority": "core",
        "default_effect": "block",
        "default_implementation_level": "full",
        "confidence_hint": "declared",
        "description": "Typical EDR prevention path for ransomware behavior.",
    },
    {
        "category": "EDR",
        "capability_code": "CAP-012",
        "optional_tags": ["Monitoring"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Additional lateral movement visibility for remote services.",
    },
    {
        "category": "EDR",
        "capability_code": "CAP-019",
        "optional_tags": ["Monitoring", "Network Traffic"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Optional beaconing and remote tool detection support.",
    },
    {
        "category": "PAM",
        "capability_code": "CAP-010",
        "optional_tags": ["Privileged Access", "Policy Enforcement"],
        "priority": "core",
        "default_effect": "prevent",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Privileged access controls commonly prevent risky privilege misuse.",
    },
    {
        "category": "PAM",
        "capability_code": "CAP-014",
        "optional_tags": ["Privileged Access", "Authentication"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Common monitoring for abuse of valid accounts.",
    },
    {
        "category": "PAM",
        "capability_code": "CAP-015",
        "optional_tags": ["Privileged Access"],
        "priority": "secondary",
        "default_effect": "prevent",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Optional session protections for privileged identity use.",
    },
    {
        "category": "DLP",
        "capability_code": "CAP-007",
        "optional_tags": ["Data Loss Prevention", "Exfiltration Control"],
        "priority": "core",
        "default_effect": "block",
        "default_implementation_level": "full",
        "confidence_hint": "declared",
        "description": "Core DLP coverage for outbound data exfiltration control.",
    },
    {
        "category": "DLP",
        "capability_code": "CAP-018",
        "optional_tags": ["Data Loss Prevention", "Email Security"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Additional email exfiltration monitoring.",
    },
    {
        "category": "DLP",
        "capability_code": "CAP-017",
        "optional_tags": ["Data Loss Prevention", "Exfiltration Control"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Additional web-based exfiltration monitoring.",
    },
    {
        "category": "SASE",
        "capability_code": "CAP-006",
        "optional_tags": ["DNS", "Network Traffic"],
        "priority": "core",
        "default_effect": "block",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Common DNS-based protection path for distributed users.",
    },
    {
        "category": "SASE",
        "capability_code": "CAP-007",
        "optional_tags": ["Data Loss Prevention", "Exfiltration Control"],
        "priority": "core",
        "default_effect": "block",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Core outbound data control for web and cloud paths.",
    },
    {
        "category": "SASE",
        "capability_code": "CAP-017",
        "optional_tags": ["Data Loss Prevention", "Network Traffic"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Optional web exfiltration analytics.",
    },
    {
        "category": "SASE",
        "capability_code": "CAP-009",
        "optional_tags": ["Authentication"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Identity-aware monitoring for mixed SASE platforms.",
    },
    {
        "category": "DNS",
        "capability_code": "CAP-006",
        "optional_tags": ["DNS"],
        "priority": "core",
        "default_effect": "block",
        "default_implementation_level": "full",
        "confidence_hint": "declared",
        "description": "Core DNS command-and-control prevention.",
    },
    {
        "category": "DNS",
        "capability_code": "CAP-019",
        "optional_tags": ["DNS", "Monitoring"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Optional DNS anomaly and beacon detection.",
    },
    {
        "category": "Email",
        "capability_code": "CAP-004",
        "optional_tags": ["Email Security", "Phishing"],
        "priority": "core",
        "default_effect": "prevent",
        "default_implementation_level": "full",
        "confidence_hint": "declared",
        "description": "Core phishing protection for inbound email.",
    },
    {
        "category": "Email",
        "capability_code": "CAP-018",
        "optional_tags": ["Email Security"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Optional email exfiltration detection and review.",
    },
    {
        "category": "BAS",
        "capability_code": "CAP-013",
        "optional_tags": ["Monitoring"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "tested",
        "description": "Common BAS starting point for ransomware validation workflows.",
    },
    {
        "category": "BAS",
        "capability_code": "CAP-009",
        "optional_tags": ["Monitoring", "Authentication"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "tested",
        "description": "Optional BAS focus area for identity misuse coverage validation.",
    },
    {
        "category": "Identity",
        "capability_code": "CAP-009",
        "optional_tags": ["Authentication", "Monitoring"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "full",
        "confidence_hint": "declared",
        "description": "Core identity monitoring for suspicious sign-in and misuse activity.",
    },
    {
        "category": "Identity",
        "capability_code": "CAP-008",
        "optional_tags": ["Authentication"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Common brute force detection for identity-centric tools.",
    },
    {
        "category": "Identity",
        "capability_code": "CAP-014",
        "optional_tags": ["Authentication"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Optional valid account abuse monitoring.",
    },
    {
        "category": "Identity",
        "capability_code": "CAP-021",
        "optional_tags": ["Active Directory"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Directory account change monitoring for AD-centric tools.",
    },
    {
        "category": "Identity",
        "capability_code": "CAP-022",
        "optional_tags": ["Active Directory", "Privileged Access"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Directory group membership monitoring for privileged groups.",
    },
    {
        "category": "Identity",
        "capability_code": "CAP-023",
        "optional_tags": ["Password Security", "Credential Hygiene"],
        "priority": "secondary",
        "default_effect": "prevent",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Credential hygiene enforcement for identity and password tools.",
    },
    {
        "category": "Identity",
        "capability_code": "CAP-024",
        "optional_tags": ["Password Security", "Credential Hygiene"],
        "priority": "core",
        "default_effect": "prevent",
        "default_implementation_level": "full",
        "confidence_hint": "declared",
        "description": "Weak password prevention for password-focused tools.",
    },
    {
        "category": "Security Analytics",
        "capability_code": "CAP-009",
        "optional_tags": ["Log Analytics", "Correlation", "Authentication"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Identity abuse detections depend on ingested identity data and maintained rules.",
    },
    {
        "category": "Security Analytics",
        "capability_code": "CAP-008",
        "optional_tags": ["Log Analytics", "Authentication"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Brute force analytics depend on authentication telemetry and rule coverage.",
    },
    {
        "category": "Security Analytics",
        "capability_code": "CAP-006",
        "optional_tags": ["Log Analytics", "DNS"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "DNS-based C2 analytics require DNS logging and maintained detections.",
    },
    {
        "category": "Security Analytics",
        "capability_code": "CAP-007",
        "optional_tags": ["Log Analytics", "Exfiltration Control"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Outbound data movement analytics rely on relevant traffic and proxy logs.",
    },
    {
        "category": "Security Analytics",
        "capability_code": "CAP-030",
        "optional_tags": ["Log Analytics", "Authentication"],
        "priority": "secondary",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Remote access abuse detection depends on remote access telemetry and rule quality.",
    },
    {
        "category": "SOAR",
        "capability_code": "CAP-026",
        "optional_tags": ["Incident Response", "Orchestration"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Operational containment workflows are only useful when upstream detections exist.",
    },
    {
        "category": "SOAR",
        "capability_code": "CAP-027",
        "optional_tags": ["Incident Response", "Authentication"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Account disable automation accelerates response to identity-related detections.",
    },
    {
        "category": "SOAR",
        "capability_code": "CAP-028",
        "optional_tags": ["Incident Response", "Orchestration"],
        "priority": "core",
        "default_effect": "detect",
        "default_implementation_level": "partial",
        "confidence_hint": "declared",
        "description": "Host isolation automation strengthens operational response once detections fire.",
    },
]

CAPABILITY_TECHNIQUE_MAPS.extend(
    [
        ("CAP-104", "T1041", "detect", "partial"),
        ("CAP-104", "T1567", "detect", "partial"),
        ("CAP-104", "T1537", "detect", "partial"),
        ("CAP-105", "T1041", "prevent", "partial"),
        ("CAP-105", "T1567", "prevent", "partial"),
        ("CAP-105", "T1537", "prevent", "partial"),
        ("CAP-117", "T1078", "detect", "partial"),
        ("CAP-117", "T1110", "detect", "partial"),
        ("CAP-124", "T1078", "prevent", "partial"),
        ("CAP-124", "T1550", "prevent", "partial"),
        ("CAP-125", "T1003", "prevent", "partial"),
        ("CAP-126", "T1078", "prevent", "partial"),
        ("CAP-126", "T1133", "prevent", "partial"),
        ("CAP-126", "T1110", "prevent", "partial"),
        ("CAP-127", "T1078", "prevent", "partial"),
        ("CAP-128", "T1078", "detect", "full"),
        ("CAP-128", "T1550", "detect", "full"),
        ("CAP-128", "T1558", "detect", "full"),
        ("CAP-128", "T1110", "detect", "full"),
        ("CAP-129", "T1078", "detect", "partial"),
        ("CAP-129", "T1098", "detect", "partial"),
        ("CAP-132", "T1098", "detect", "full"),
        ("CAP-132", "T1484", "detect", "full"),
        ("CAP-132", "T1136", "detect", "full"),
        ("CAP-133", "T1078", "detect", "partial"),
        ("CAP-133", "T1133", "detect", "partial"),
        ("CAP-133", "T1087", "detect", "partial"),
        ("CAP-134", "T1078", "detect", "partial"),
        ("CAP-134", "T1110", "detect", "partial"),
        ("CAP-134", "T1071", "detect", "partial"),
        ("CAP-134", "T1041", "detect", "partial"),
        ("CAP-135", "T1078", "detect", "partial"),
        ("CAP-135", "T1071", "detect", "partial"),
        ("CAP-135", "T1041", "detect", "partial"),
    ]
)

CAPABILITY_CODE_SET = {capability["code"] for capability in CAPABILITIES}
TECHNIQUE_CODE_SET = {technique["code"] for technique in TECHNIQUES}
DATA_SOURCE_CODE_SET = {data_source["code"] for data_source in DATA_SOURCES}
RESPONSE_ACTION_CODE_SET = {action["code"] for action in RESPONSE_ACTIONS}
COVERAGE_SCOPE_CODE_SET = {scope["code"] for scope in COVERAGE_SCOPES}
VENDOR_NAME_SET = {vendor["name"] for vendor in VENDORS}
COVERAGE_ROLE_CODE_SET = {role["code"] for role in COVERAGE_ROLES}

LEGACY_CAPABILITY_MAP = {
    "CAP-001": ("CAP-001", "detect"),
    "CAP-002": ("CAP-001", "block"),
    "CAP-003": ("CAP-002", "detect"),
    "CAP-004": ("CAP-002", "block"),
    "CAP-005": ("CAP-003", "detect"),
    "CAP-006": ("CAP-003", "block"),
    "CAP-007": ("CAP-004", "detect"),
    "CAP-008": ("CAP-004", "prevent"),
    "CAP-009": ("CAP-005", "detect"),
    "CAP-010": ("CAP-006", "detect"),
    "CAP-011": ("CAP-006", "block"),
    "CAP-012": ("CAP-007", "detect"),
    "CAP-013": ("CAP-007", "block"),
    "CAP-014": ("CAP-008", "detect"),
    "CAP-015": ("CAP-009", "detect"),
    "CAP-016": ("CAP-010", "prevent"),
    "CAP-017": ("CAP-011", "detect"),
    "CAP-018": ("CAP-012", "detect"),
    "CAP-019": ("CAP-013", "detect"),
    "CAP-020": ("CAP-013", "block"),
}


def _normalize_capability_name(name: str) -> str:
    return "".join(character for character in name.casefold() if character.isalnum())


def _upsert_reference_rows(db: Session, model, rows: list[dict[str, object]]) -> None:
    existing_rows = {
        row.code: row
        for row in db.scalars(select(model)).all()
    }
    for row in rows:
        existing = existing_rows.get(row["code"])
        if existing is None:
            db.add(model(**row))
            continue
        for field, value in row.items():
            setattr(existing, field, value)


def _upsert_named_rows(db: Session, model, rows: list[dict[str, object]]) -> None:
    existing_rows = {
        row.name: row
        for row in db.scalars(select(model)).all()
    }
    for row in rows:
        existing = existing_rows.get(row["name"])
        if existing is None:
            db.add(model(**row))
            continue
        for field, value in row.items():
            setattr(existing, field, value)


def _apply_named_capability_mapping_patches(db: Session) -> None:
    capabilities = db.scalars(select(Capability)).all()
    techniques = {
        technique.code: technique
        for technique in db.scalars(select(Technique)).all()
    }
    capability_by_name = {capability.name: capability for capability in capabilities}
    capability_by_normalized_name = {
        _normalize_capability_name(capability.name): capability
        for capability in capabilities
    }
    existing_mappings = {
        (mapping.capability_id, mapping.technique_id, mapping.control_effect)
        for mapping in db.scalars(select(CapabilityTechniqueMap)).all()
    }

    missing_techniques = sorted(
        {
            technique_code
            for mapping_entries in CAPABILITY_MAPPING_PATCHES_BY_NAME.values()
            for technique_code, _, _ in mapping_entries
            if technique_code not in techniques
        }
    )
    if missing_techniques:
        raise ValueError(
            "Cannot apply capability mapping patches because these ATT&CK techniques are missing: "
            + ", ".join(missing_techniques)
        )

    summary_lines: list[str] = []
    added_count = 0

    for capability_name, mapping_entries in CAPABILITY_MAPPING_PATCHES_BY_NAME.items():
        capability = capability_by_name.get(capability_name) or capability_by_normalized_name.get(
            _normalize_capability_name(capability_name)
        )
        if capability is None:
            summary_lines.append(f"[mapping] capability not found: {capability_name}")
            continue

        linked_techniques: list[str] = []
        skipped_techniques: list[str] = []
        for technique_code, control_effect, coverage in mapping_entries:
            mapping_key = (capability.id, techniques[technique_code].id, control_effect)
            if mapping_key in existing_mappings:
                skipped_techniques.append(f"{technique_code}/{control_effect}")
                continue

            db.add(
                CapabilityTechniqueMap(
                    capability_id=capability.id,
                    technique_id=techniques[technique_code].id,
                    control_effect=control_effect,
                    coverage=coverage,
                )
            )
            existing_mappings.add(mapping_key)
            linked_techniques.append(f"{technique_code}/{control_effect}")
            added_count += 1

        found_message = f"[mapping] capability found: {capability.name}"
        if linked_techniques:
            found_message += f" | linked: {', '.join(linked_techniques)}"
        if skipped_techniques:
            found_message += f" | skipped existing: {', '.join(skipped_techniques)}"
        summary_lines.append(found_message)

    if added_count:
        db.commit()

    if added_count or any("not found" in line for line in summary_lines):
        for line in summary_lines:
            print(line)


def sync_reference_data(db: Session) -> None:
    capability_codes = {code for (code,) in db.execute(select(Capability.code)).all()}
    technique_codes = {code for (code,) in db.execute(select(Technique.code)).all()}
    data_source_codes = {code for (code,) in db.execute(select(DataSource.code)).all()}
    response_action_codes = {code for (code,) in db.execute(select(ResponseAction.code)).all()}
    coverage_scope_codes = {code for (code,) in db.execute(select(CoverageScope.code)).all()}
    vendor_names = {name for (name,) in db.execute(select(Vendor.name)).all()}
    coverage_role_codes = {code for (code,) in db.execute(select(CoverageRole.code)).all()}

    if (
        capability_codes == CAPABILITY_CODE_SET
        and technique_codes == TECHNIQUE_CODE_SET
        and data_source_codes == DATA_SOURCE_CODE_SET
        and response_action_codes == RESPONSE_ACTION_CODE_SET
        and coverage_scope_codes == COVERAGE_SCOPE_CODE_SET
        and VENDOR_NAME_SET.issubset(vendor_names)
        and coverage_role_codes == COVERAGE_ROLE_CODE_SET
    ):
        return

    _upsert_reference_rows(db, Capability, CAPABILITIES)
    _upsert_reference_rows(db, Technique, TECHNIQUES)
    _upsert_reference_rows(db, DataSource, DATA_SOURCES)
    _upsert_reference_rows(db, ResponseAction, RESPONSE_ACTIONS)
    _upsert_reference_rows(db, CoverageScope, COVERAGE_SCOPES)
    _upsert_named_rows(db, Vendor, VENDORS)
    _upsert_reference_rows(db, CoverageRole, COVERAGE_ROLES)
    db.commit()

    seed_reference_data(db)


def seed_reference_data(db: Session) -> None:
    if not db.scalar(select(Capability.id).limit(1)):
        db.add_all(Capability(**capability) for capability in CAPABILITIES)
        db.commit()

    if not db.scalar(select(Technique.id).limit(1)):
        db.add_all(Technique(**technique) for technique in TECHNIQUES)
        db.commit()

    if not db.scalar(select(DataSource.id).limit(1)):
        db.add_all(DataSource(**data_source) for data_source in DATA_SOURCES)
        db.commit()

    if not db.scalar(select(ResponseAction.id).limit(1)):
        db.add_all(ResponseAction(**action) for action in RESPONSE_ACTIONS)
        db.commit()

    if not db.scalar(select(CoverageScope.id).limit(1)):
        db.add_all(CoverageScope(**scope) for scope in COVERAGE_SCOPES)
        db.commit()

    if not db.scalar(select(Vendor.id).limit(1)):
        db.add_all(Vendor(**vendor) for vendor in VENDORS)
        db.commit()

    if not db.scalar(select(CoverageRole.id).limit(1)):
        db.add_all(CoverageRole(**role) for role in COVERAGE_ROLES)
        db.commit()

    _seed_capability_technique_maps(db)
    _seed_technique_relevant_scopes(db)
    _seed_capability_dependencies(db)
    _seed_capability_coverage_roles(db)
    _seed_assessment_templates(db)
    _seed_configuration_questions(db)
    _seed_tool_capability_templates(db)
    _normalize_known_tools(db)


def _seed_capability_technique_maps(db: Session) -> None:
    capabilities = {
        capability.code: capability
        for capability in db.scalars(select(Capability)).all()
    }
    techniques = {
        technique.code: technique
        for technique in db.scalars(select(Technique)).all()
    }
    existing_mappings = {
        (mapping.capability_id, mapping.technique_id, mapping.control_effect)
        for mapping in db.scalars(select(CapabilityTechniqueMap)).all()
    }

    added = False
    for capability_code, technique_code, control_effect, coverage in CAPABILITY_TECHNIQUE_MAPS:
        mapping_key = (capabilities[capability_code].id, techniques[technique_code].id, control_effect)
        if mapping_key in existing_mappings:
            continue
        db.add(
            CapabilityTechniqueMap(
                capability_id=capabilities[capability_code].id,
                technique_id=techniques[technique_code].id,
                control_effect=control_effect,
                coverage=coverage,
            )
        )
        existing_mappings.add(mapping_key)
        added = True

    if added:
        db.commit()

    _apply_named_capability_mapping_patches(db)


def _seed_technique_relevant_scopes(db: Session) -> None:
    techniques = {technique.code: technique for technique in db.scalars(select(Technique)).all()}
    scopes = {scope.code: scope for scope in db.scalars(select(CoverageScope)).all()}
    existing_links = {
        (link.technique_id, link.coverage_scope_id, link.relevance)
        for link in db.scalars(select(TechniqueRelevantScope)).all()
    }

    added = False
    for technique_code, scope_code, relevance in TECHNIQUE_RELEVANT_SCOPES:
        link_key = (techniques[technique_code].id, scopes[scope_code].id, relevance)
        if link_key in existing_links:
            continue
        db.add(
            TechniqueRelevantScope(
                technique_id=techniques[technique_code].id,
                coverage_scope_id=scopes[scope_code].id,
                relevance=relevance,
            )
        )
        existing_links.add(link_key)
        added = True

    if added:
        db.commit()


def _seed_assessment_templates(db: Session) -> None:
    existing_template_count = db.query(CapabilityAssessmentTemplate).count()
    if existing_template_count == len(CAPABILITY_ASSESSMENT_TEMPLATES):
        return

    if existing_template_count:
        db.query(CapabilityAssessmentQuestion).delete()
        db.query(CapabilityAssessmentTemplate).delete()
        db.commit()

    capabilities = {
        capability.code: capability
        for capability in db.scalars(select(Capability)).all()
    }

    for capability_code, template_data in CAPABILITY_ASSESSMENT_TEMPLATES.items():
        template = CapabilityAssessmentTemplate(
            capability_id=capabilities[capability_code].id,
            description=template_data["description"],
        )
        db.add(template)
        db.flush()

        db.add_all(
            CapabilityAssessmentQuestion(
                template_id=template.id,
                prompt=prompt,
                position=index,
            )
            for index, prompt in enumerate(template_data["questions"], start=1)
        )

    db.commit()


def _seed_configuration_questions(db: Session) -> None:
    expected_count = sum(len(item["questions"]) for item in CAPABILITY_CONFIGURATION_QUESTIONS.values())
    existing_count = db.query(CapabilityConfigurationQuestion).count()
    if existing_count == expected_count:
        return

    if existing_count:
        db.query(CapabilityConfigurationQuestion).delete()
        db.commit()

    capabilities = {
        capability.code: capability
        for capability in db.scalars(select(Capability)).all()
    }

    for capability_code, template_data in CAPABILITY_CONFIGURATION_QUESTIONS.items():
        capability = capabilities[capability_code]
        for prompt in template_data["questions"]:
            db.add(
                CapabilityConfigurationQuestion(
                    capability_id=capability.id,
                    question=prompt,
                    applies_to_profile_type=template_data["profile_type"],
                )
            )

    db.commit()


def _seed_capability_dependencies(db: Session) -> None:
    existing_required_count = db.query(CapabilityRequiredDataSource).count()
    if existing_required_count != len(CAPABILITY_REQUIRED_DATA_SOURCES):
        if existing_required_count:
            db.query(CapabilityRequiredDataSource).delete()
            db.commit()

        capabilities = {
            capability.code: capability
            for capability in db.scalars(select(Capability)).all()
        }
        data_sources = {
            data_source.code: data_source
            for data_source in db.scalars(select(DataSource)).all()
        }
        db.add_all(
            CapabilityRequiredDataSource(
                capability_id=capabilities[capability_code].id,
                data_source_id=data_sources[data_source_code].id,
                requirement_level=requirement_level,
            )
            for capability_code, data_source_code, requirement_level in CAPABILITY_REQUIRED_DATA_SOURCES
        )
        db.commit()

    existing_response_count = db.query(CapabilitySupportedResponseAction).count()
    if existing_response_count != len(CAPABILITY_SUPPORTED_RESPONSE_ACTIONS):
        if existing_response_count:
            db.query(CapabilitySupportedResponseAction).delete()
            db.commit()

        capabilities = {
            capability.code: capability
            for capability in db.scalars(select(Capability)).all()
        }
        response_actions = {
            action.code: action
            for action in db.scalars(select(ResponseAction)).all()
        }
        db.add_all(
            CapabilitySupportedResponseAction(
                capability_id=capabilities[capability_code].id,
                response_action_id=response_actions[action_code].id,
            )
            for capability_code, action_code in CAPABILITY_SUPPORTED_RESPONSE_ACTIONS
        )
        db.commit()


def _seed_capability_coverage_roles(db: Session) -> None:
    capabilities_by_name = {capability.name: capability for capability in db.scalars(select(Capability)).all()}
    roles_by_code = {role.code: role for role in db.scalars(select(CoverageRole)).all()}
    existing_links = {
        (link.capability_id, link.coverage_role_id)
        for link in db.scalars(select(CapabilityCoverageRole)).all()
    }

    added = False
    for capability_name, role_codes in CAPABILITY_COVERAGE_ROLE_ASSIGNMENTS.items():
        capability = capabilities_by_name.get(capability_name)
        if capability is None:
            continue
        for role_code in role_codes:
            role = roles_by_code.get(role_code)
            if role is None:
                continue
            link_key = (capability.id, role.id)
            if link_key in existing_links:
                continue
            db.add(
                CapabilityCoverageRole(
                    capability_id=capability.id,
                    coverage_role_id=role.id,
                )
            )
            existing_links.add(link_key)
            added = True

    if added:
        db.commit()


def _normalize_known_tools(db: Session) -> None:
    tools_by_name = {tool.name: tool for tool in db.scalars(select(Tool)).all()}
    vendors_by_name = {vendor.name: vendor for vendor in db.scalars(select(Vendor)).all()}
    capabilities_by_name = {capability.name: capability for capability in db.scalars(select(Capability)).all()}

    for rule in TOOL_CAPABILITY_NORMALIZATION_RULES:
        tool = tools_by_name.get(rule["tool_name"])
        if tool is None:
            continue

        vendor = vendors_by_name.get(rule["vendor_name"])
        if vendor is not None and tool.vendor_id != vendor.id:
            tool.vendor_id = vendor.id

        if tool.category == "Other" and rule["category"] != "Other":
            tool.category = rule["category"]

        tool.tool_types = list(dict.fromkeys([*tool.tool_types, *rule["tool_types"]]))
        tool.tool_type_labels = list(dict.fromkeys([*tool.tool_type_labels, *rule["tool_type_labels"]]))

        assignments_by_capability_id = {
            assignment.capability_id: assignment
            for assignment in tool.capabilities
        }
        linked_messages: list[str] = []
        skipped_messages: list[str] = []

        for capability_name, control_effect, implementation_level in rule["capabilities"]:
            capability = capabilities_by_name.get(capability_name)
            if capability is None:
                skipped_messages.append(f"{capability_name} (missing capability)")
                continue

            assignment = assignments_by_capability_id.get(capability.id)
            if assignment is None:
                db.add(
                    ToolCapability(
                        tool_id=tool.id,
                        capability_id=capability.id,
                        control_effect_default=control_effect,
                        implementation_level=implementation_level,
                    )
                )
                linked_messages.append(f"{capability_name} -> {control_effect}/{implementation_level}")
            else:
                skipped_messages.append(f"{capability_name} (already linked)")

        db.flush()
        print(
            "[tool-normalization] "
            f"{tool.name}"
            + (f" | linked: {', '.join(linked_messages)}" if linked_messages else "")
            + (f" | skipped: {', '.join(skipped_messages)}" if skipped_messages else "")
        )

    db.commit()


def _seed_tool_capability_templates(db: Session) -> None:
    existing_template_count = db.query(ToolCapabilityTemplate).count()
    if existing_template_count == len(TOOL_CAPABILITY_TEMPLATES):
        return

    if existing_template_count:
        db.query(ToolCapabilityTemplate).delete()
        db.commit()

    capabilities = {
        capability.code: capability
        for capability in db.scalars(select(Capability)).all()
    }

    db.add_all(
        ToolCapabilityTemplate(
            category=template["category"],
            capability_id=capabilities[template["capability_code"]].id,
            optional_tags=template["optional_tags"],
            priority=template["priority"],
            default_effect=template["default_effect"],
            default_implementation_level=template["default_implementation_level"],
            confidence_hint=template["confidence_hint"],
            description=template["description"],
        )
        for template in TOOL_CAPABILITY_TEMPLATES
    )
    db.commit()


def get_supported_effects_for_capability(capability_code: str) -> Sequence[str]:
    return [
        control_effect
        for mapped_capability_code, _, control_effect, _ in CAPABILITY_TECHNIQUE_MAPS
        if mapped_capability_code == capability_code
    ]
