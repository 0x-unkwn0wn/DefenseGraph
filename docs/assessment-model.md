# Assessment Model

DefenseGraph supports capability-specific assessments with vendor-neutral questions.

## Data model

- `CapabilityAssessmentTemplate`
  - one template per capability
  - stores template description

- `CapabilityAssessmentQuestion`
  - belongs to a template
  - stores prompt and display order

- `ToolCapabilityAssessmentAnswer`
  - belongs to a specific `ToolCapability`
  - stores one answer per question

## Answer values

- `yes`
- `no`
- `partial`
- `unknown`

## Current seeded capabilities

The MVP ships guided assessments for:

- Email Phishing Protection
- DNS C2 Control
- Credential Dumping Protection
- Data Exfiltration Protection
- Script Execution Control
- Ransomware Protection
- Identity Misuse Detection
- Brute Force Detection

## UX model

- Assessments are answered from tool detail, inside the capability workspace.
- Capability detail exposes the same template so the capability can be reviewed as a central node.
- Saving assessment answers recalculates confidence immediately.
