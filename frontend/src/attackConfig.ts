import type {
  ControlEffect,
  MappingCoverage,
  TacticName,
  TechniqueDisplayGroup,
} from "./types";

export interface AttackTechniqueDefinition {
  code: string;
  tactic: TacticName;
  displayGroup: TechniqueDisplayGroup;
}

export const tacticOrder: TacticName[] = [
  "Initial Access",
  "Execution",
  "Persistence / Privilege Escalation / Defense Evasion",
  "Credential Access",
  "Discovery",
  "Lateral Movement",
  "Command & Control",
  "Collection / Exfiltration",
  "Impact",
];

export const attackTechniqueCatalog: AttackTechniqueDefinition[] = [
  { code: "T1566", tactic: "Initial Access", displayGroup: "core" },
  { code: "T1190", tactic: "Initial Access", displayGroup: "extended" },
  { code: "T1133", tactic: "Initial Access", displayGroup: "core" },
  { code: "T1059", tactic: "Execution", displayGroup: "core" },
  { code: "T1059.001", tactic: "Execution", displayGroup: "core" },
  { code: "T1059.003", tactic: "Execution", displayGroup: "extended" },
  { code: "T1204", tactic: "Execution", displayGroup: "core" },
  {
    code: "T1547",
    tactic: "Persistence / Privilege Escalation / Defense Evasion",
    displayGroup: "core",
  },
  {
    code: "T1055",
    tactic: "Persistence / Privilege Escalation / Defense Evasion",
    displayGroup: "extended",
  },
  {
    code: "T1068",
    tactic: "Persistence / Privilege Escalation / Defense Evasion",
    displayGroup: "extended",
  },
  {
    code: "T1136",
    tactic: "Persistence / Privilege Escalation / Defense Evasion",
    displayGroup: "extended",
  },
  {
    code: "T1098",
    tactic: "Persistence / Privilege Escalation / Defense Evasion",
    displayGroup: "extended",
  },
  {
    code: "T1484",
    tactic: "Persistence / Privilege Escalation / Defense Evasion",
    displayGroup: "extended",
  },
  { code: "T1003", tactic: "Credential Access", displayGroup: "core" },
  { code: "T1003.006", tactic: "Credential Access", displayGroup: "extended" },
  { code: "T1110", tactic: "Credential Access", displayGroup: "core" },
  { code: "T1550", tactic: "Credential Access", displayGroup: "core" },
  { code: "T1558", tactic: "Credential Access", displayGroup: "core" },
  { code: "T1087", tactic: "Discovery", displayGroup: "core" },
  { code: "T1082", tactic: "Discovery", displayGroup: "extended" },
  { code: "T1016", tactic: "Discovery", displayGroup: "extended" },
  { code: "T1135", tactic: "Discovery", displayGroup: "extended" },
  { code: "T1021", tactic: "Lateral Movement", displayGroup: "core" },
  { code: "T1078", tactic: "Lateral Movement", displayGroup: "core" },
  { code: "T1570", tactic: "Lateral Movement", displayGroup: "extended" },
  { code: "T1071", tactic: "Command & Control", displayGroup: "core" },
  { code: "T1071.004", tactic: "Command & Control", displayGroup: "core" },
  { code: "T1568", tactic: "Command & Control", displayGroup: "core" },
  { code: "T1090", tactic: "Command & Control", displayGroup: "extended" },
  { code: "T1105", tactic: "Command & Control", displayGroup: "extended" },
  { code: "T1114", tactic: "Collection / Exfiltration", displayGroup: "extended" },
  { code: "T1041", tactic: "Collection / Exfiltration", displayGroup: "core" },
  { code: "T1567", tactic: "Collection / Exfiltration", displayGroup: "core" },
  { code: "T1537", tactic: "Collection / Exfiltration", displayGroup: "core" },
  { code: "T1486", tactic: "Impact", displayGroup: "core" },
];

export const techniqueTactics: Record<string, TacticName> = Object.fromEntries(
  attackTechniqueCatalog.map((technique) => [technique.code, technique.tactic]),
) as Record<string, TacticName>;

export const techniqueDisplayGroups: Record<string, TechniqueDisplayGroup> = Object.fromEntries(
  attackTechniqueCatalog.map((technique) => [technique.code, technique.displayGroup]),
) as Record<string, TechniqueDisplayGroup>;

export const coreTechniqueCodes = attackTechniqueCatalog
  .filter((technique) => technique.displayGroup === "core")
  .map((technique) => technique.code);

export const extendedTechniqueCodes = attackTechniqueCatalog
  .filter((technique) => technique.displayGroup === "extended")
  .map((technique) => technique.code);

type SupportedEffect = Exclude<ControlEffect, "none">;

export interface CapabilityTechniqueDefinition {
  capabilityCode: string;
  techniqueCode: string;
  controlEffect: SupportedEffect;
  mappingCoverage: MappingCoverage;
}

export const capabilityTechniqueDefinitions: CapabilityTechniqueDefinition[] = [
  { capabilityCode: "CAP-001", techniqueCode: "T1059", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-001", techniqueCode: "T1059", controlEffect: "block", mappingCoverage: "full" },
  { capabilityCode: "CAP-001", techniqueCode: "T1059.003", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-001", techniqueCode: "T1059.003", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-001", techniqueCode: "T1204", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-001", techniqueCode: "T1055", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-001", techniqueCode: "T1547", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-002", techniqueCode: "T1059.001", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-002", techniqueCode: "T1059.001", controlEffect: "block", mappingCoverage: "full" },
  { capabilityCode: "CAP-003", techniqueCode: "T1003", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-003", techniqueCode: "T1003", controlEffect: "block", mappingCoverage: "full" },
  { capabilityCode: "CAP-003", techniqueCode: "T1003.006", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-003", techniqueCode: "T1003.006", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-004", techniqueCode: "T1566", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-004", techniqueCode: "T1566", controlEffect: "prevent", mappingCoverage: "full" },
  { capabilityCode: "CAP-004", techniqueCode: "T1204", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-004", techniqueCode: "T1204", controlEffect: "prevent", mappingCoverage: "full" },
  { capabilityCode: "CAP-005", techniqueCode: "T1071", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-005", techniqueCode: "T1568", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-005", techniqueCode: "T1090", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-006", techniqueCode: "T1071.004", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-006", techniqueCode: "T1071.004", controlEffect: "block", mappingCoverage: "full" },
  { capabilityCode: "CAP-006", techniqueCode: "T1568", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-006", techniqueCode: "T1568", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-007", techniqueCode: "T1041", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-007", techniqueCode: "T1041", controlEffect: "block", mappingCoverage: "full" },
  { capabilityCode: "CAP-007", techniqueCode: "T1114", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-008", techniqueCode: "T1110", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-008", techniqueCode: "T1110", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-009", techniqueCode: "T1078", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-009", techniqueCode: "T1558", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-009", techniqueCode: "T1087", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-009", techniqueCode: "T1003.006", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-010", techniqueCode: "T1078", controlEffect: "prevent", mappingCoverage: "partial" },
  { capabilityCode: "CAP-010", techniqueCode: "T1550", controlEffect: "prevent", mappingCoverage: "full" },
  { capabilityCode: "CAP-010", techniqueCode: "T1558", controlEffect: "prevent", mappingCoverage: "partial" },
  { capabilityCode: "CAP-010", techniqueCode: "T1098", controlEffect: "prevent", mappingCoverage: "partial" },
  { capabilityCode: "CAP-010", techniqueCode: "T1484", controlEffect: "prevent", mappingCoverage: "partial" },
  { capabilityCode: "CAP-011", techniqueCode: "T1550", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-011", techniqueCode: "T1558", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-012", techniqueCode: "T1133", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-012", techniqueCode: "T1133", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-012", techniqueCode: "T1021", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-012", techniqueCode: "T1021", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-012", techniqueCode: "T1570", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-012", techniqueCode: "T1135", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-013", techniqueCode: "T1486", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-013", techniqueCode: "T1486", controlEffect: "block", mappingCoverage: "full" },
  { capabilityCode: "CAP-014", techniqueCode: "T1078", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-014", techniqueCode: "T1078", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-015", techniqueCode: "T1550", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-015", techniqueCode: "T1550", controlEffect: "prevent", mappingCoverage: "partial" },
  { capabilityCode: "CAP-015", techniqueCode: "T1558", controlEffect: "prevent", mappingCoverage: "partial" },
  { capabilityCode: "CAP-016", techniqueCode: "T1204", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-016", techniqueCode: "T1059", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-016", techniqueCode: "T1059.001", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-016", techniqueCode: "T1059.003", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-017", techniqueCode: "T1567", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-017", techniqueCode: "T1567", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-018", techniqueCode: "T1537", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-018", techniqueCode: "T1537", controlEffect: "prevent", mappingCoverage: "partial" },
  { capabilityCode: "CAP-018", techniqueCode: "T1114", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-019", techniqueCode: "T1071", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-019", techniqueCode: "T1071.004", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-019", techniqueCode: "T1568", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-019", techniqueCode: "T1090", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-020", techniqueCode: "T1055", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-020", techniqueCode: "T1547", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-020", techniqueCode: "T1068", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-020", techniqueCode: "T1082", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-020", techniqueCode: "T1016", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-020", techniqueCode: "T1486", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-020", techniqueCode: "T1021", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-021", techniqueCode: "T1078", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-021", techniqueCode: "T1087", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-021", techniqueCode: "T1136", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-021", techniqueCode: "T1098", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-021", techniqueCode: "T1484", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-022", techniqueCode: "T1078", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-022", techniqueCode: "T1087", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-022", techniqueCode: "T1484", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-023", techniqueCode: "T1110", controlEffect: "prevent", mappingCoverage: "partial" },
  { capabilityCode: "CAP-024", techniqueCode: "T1110", controlEffect: "prevent", mappingCoverage: "full" },
  { capabilityCode: "CAP-025", techniqueCode: "T1190", controlEffect: "detect", mappingCoverage: "full" },
  { capabilityCode: "CAP-025", techniqueCode: "T1190", controlEffect: "block", mappingCoverage: "partial" },
  { capabilityCode: "CAP-025", techniqueCode: "T1133", controlEffect: "detect", mappingCoverage: "partial" },
  { capabilityCode: "CAP-025", techniqueCode: "T1133", controlEffect: "block", mappingCoverage: "partial" },
];
