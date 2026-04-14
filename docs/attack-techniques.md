# DefenseGraph ATT&CK catalog

DefenseGraph uses a curated catalog of 34 Enterprise ATT&CK techniques and sub-techniques. The product shows a high-signal Core subset by default and keeps the rest available as Extended techniques when deeper review is needed.

## Why Core and Extended exist

- Core keeps the default matrix compact enough for fast scanning.
- Extended adds realism for common adjacent behaviors without forcing a full ATT&CK navigator experience.
- The split is a display choice only. Coverage, gaps, and mappings still use one shared ATT&CK catalog.

## Core techniques

| Tactic bucket | Techniques |
| --- | --- |
| Initial Access | `T1566` Phishing, `T1133` External Remote Services |
| Execution | `T1059` Command and Scripting Interpreter, `T1059.001` PowerShell, `T1204` User Execution |
| Persistence / Privilege Escalation / Defense Evasion | `T1547` Boot or Logon Autostart Execution |
| Credential Access | `T1003` OS Credential Dumping, `T1110` Brute Force, `T1550` Use Alternate Authentication Material, `T1558` Steal or Forge Kerberos Tickets |
| Discovery | `T1087` Account Discovery |
| Lateral Movement | `T1021` Remote Services, `T1078` Valid Accounts |
| Command & Control | `T1071` Application Layer Protocol, `T1071.004` DNS, `T1568` Dynamic Resolution |
| Collection / Exfiltration | `T1041` Exfiltration Over C2 Channel, `T1567` Exfiltration Over Web Service, `T1537` Exfiltration via Email |
| Impact | `T1486` Data Encrypted for Impact |

## Extended techniques

| Tactic bucket | Techniques |
| --- | --- |
| Initial Access | `T1190` Exploit Public-Facing Application |
| Execution | `T1059.003` Windows Command Shell |
| Persistence / Privilege Escalation / Defense Evasion | `T1055` Process Injection, `T1068` Exploitation for Privilege Escalation, `T1136` Create Account, `T1098` Account Manipulation, `T1484` Domain or Group Policy Modification |
| Credential Access | `T1003.006` DCSync |
| Discovery | `T1082` System Information Discovery, `T1016` System Network Configuration Discovery, `T1135` Network Share Discovery |
| Lateral Movement | `T1570` Lateral Tool Transfer |
| Command & Control | `T1090` Proxy |
| Collection / Exfiltration | `T1114` Email Collection |

## Mapping philosophy

- Capabilities remain neutral and product-oriented instead of ATT&CK-native.
- Every technique in the catalog has at least one capability mapping.
- Strong mappings use `detect`, `block`, or `prevent` where the control is directly credible.
- Weaker coverage stays partial and confidence-sensitive rather than pretending to be stronger than it is.
- The matrix groups techniques into simplified tactic buckets so the UI stays readable even with 34 techniques.
