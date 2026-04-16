# ATT&CK Capability Taxonomy

Updated: 2026-04-16

## Why this exists

Enterprise ATT&CK is now loaded locally with `691` techniques and sub-techniques.
Only `35` of them are currently mapped to capabilities, so the scaling problem is no longer ATT&CK ingestion.
It is the capability taxonomy.

This repo now uses `Capability.family` to avoid creating one capability per ATT&CK item.
Families are intended to be reusable mapping buckets that can cover clusters of related ATT&CK techniques and sub-techniques.

## Current gap shape

- Unmapped ATT&CK items: `656`
- Unmapped parent techniques: `185`
- Unmapped sub-techniques: `471`
- Unmapped sub-techniques under already known parents: `114`

Largest unmapped ATT&CK clusters observed in the local database:

- `T1546` Event Triggered Execution
- `T1027` Obfuscated Files or Information
- `T1218` System Binary Proxy Execution
- `T1547` Boot or Logon Autostart Execution
- `T1564` Hide Artifacts
- `T1036` Masquerading
- `T1055` Process Injection
- `T1562` Impair Defenses
- `T1574` Hijack Execution Flow
- `T1556` Modify Authentication Process
- `T1583` Acquire Infrastructure
- `T1584` Compromise Infrastructure

Dominant unmapped tactic pressure:

- Defense Evasion
- Persistence
- Privilege Escalation
- Credential Access
- Resource Development
- Discovery
- Reconnaissance

## Families introduced

The capability catalog now uses these families:

- `Endpoint Execution & Scripting`
- `Credential & Secret Protection`
- `Email Security`
- `Command & Control`
- `Data Exfiltration & Governance`
- `Identity Threat Detection`
- `Privileged Access & Session Control`
- `Remote Services & Lateral Movement`
- `Endpoint Impact Protection`
- `Application Exposure Protection`
- `Response Orchestration`
- `Network Segmentation & Access`
- `Device Compliance & Hardening`
- `Directory Security Assessment`
- `Credential Hygiene & Identity Posture`
- `Identity Administration & Change Control`
- `Network Exposure Assessment`
- `Security Analytics`
- `Endpoint Evasion & Defense Impairment`
- `Endpoint Persistence & Autoruns`
- `Process Injection & Execution Hijack`
- `Endpoint Collection & Capture`
- `Authentication Artifact Abuse`
- `Network Tunneling & Remote Access`
- `Cloud & SaaS Control Plane`
- `Pre-Attack Recon & Resource Development`
- `Application & API Component Abuse`

## First expansion wave

The first seeded wave adds capabilities aimed at the biggest unmapped ATT&CK groups instead of adding one-off controls:

- `CAP-136` LOLBins and Proxy Execution Control
- `CAP-137` Artifact Hiding and Cleanup Detection
- `CAP-138` Event-Triggered Execution Protection
- `CAP-139` Boot and Logon Autostart Control
- `CAP-140` Process Injection Detection
- `CAP-141` Execution Flow Hijack Detection
- `CAP-142` Masquerading Detection
- `CAP-143` Defense Impairment Protection
- `CAP-144` Endpoint Collection and Capture Monitoring
- `CAP-145` Staging and Automated Exfiltration Monitoring
- `CAP-146` Destructive Impact and Recovery Protection
- `CAP-147` Password Store and Secret Access Protection
- `CAP-148` Authentication Process Tampering Detection
- `CAP-149` Token, Cookie, and Session Abuse Detection
- `CAP-150` Certificate and Key Abuse Detection
- `CAP-151` Protocol Tunneling and Encrypted C2 Detection
- `CAP-152` Remote Admin Tool and RAT Detection
- `CAP-153` Network Sniffing and Discovery Detection
- `CAP-154` Cloud Control Plane Abuse Detection
- `CAP-155` SaaS and Cloud Repository Abuse Detection
- `CAP-156` Container and Serverless Execution Detection
- `CAP-157` Public-Facing Application Component Abuse Detection
- `CAP-158` Reconnaissance and Victim Discovery Monitoring
- `CAP-159` Infrastructure Acquisition and Staging Monitoring

## How to use it

Recommended mapping order:

1. Finish the sub-technique-heavy endpoint evasion and persistence families.
2. Expand identity mapping around tokens, cookies, secrets, and authentication tampering.
3. Cover network tunneling, remote admin tooling, and discovery.
4. Add cloud, SaaS, and application-component mappings.
5. Use pre-attack families only in views that intentionally include external exposure and resource-development coverage.

Important rule:

Map at the `sub-technique` level when it exists.
Parent techniques should be aggregated visually, not treated as automatically covered.
