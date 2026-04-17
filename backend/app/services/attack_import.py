from __future__ import annotations

import logging
from collections.abc import Sequence

logger = logging.getLogger(__name__)

DEFAULT_ATTACK_URL = (
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/"
    "enterprise-attack/enterprise-attack.json"
)


def build_attack_url(attack_id: str) -> str:
    return f"https://attack.mitre.org/techniques/{attack_id.replace('.', '/')}/"


def format_attack_tactic(phase_name: str) -> str:
    return phase_name.replace("-", " ").replace("&", "and").title().replace("And", "&")


def extract_attack_id(stix_object: dict[str, object]) -> str | None:
    for reference in stix_object.get("external_references", []):
        if (
            isinstance(reference, dict)
            and reference.get("source_name") == "mitre-attack"
            and isinstance(reference.get("external_id"), str)
        ):
            return reference["external_id"]
    return None


def iter_enterprise_attack_techniques_from_bundle(
    bundle: dict[str, object],
    *,
    core_codes: Sequence[str] = (),
    extended_codes: Sequence[str] = (),
) -> list[dict[str, object]]:
    objects = [
        item
        for item in bundle.get("objects", [])
        if isinstance(item, dict)
    ]
    attack_patterns = [
        item
        for item in objects
        if item.get("type") == "attack-pattern"
        and "enterprise-attack" in item.get("x_mitre_domains", [])
        and not bool(item.get("revoked"))
        and not bool(item.get("x_mitre_deprecated"))
    ]

    stix_id_to_attack_id = {
        item["id"]: attack_id
        for item in attack_patterns
        if isinstance(item.get("id"), str) and (attack_id := extract_attack_id(item))
    }
    parent_map = {
        item["source_ref"]: stix_id_to_attack_id.get(item["target_ref"])
        for item in objects
        if item.get("type") == "relationship"
        and item.get("relationship_type") == "subtechnique-of"
        and isinstance(item.get("source_ref"), str)
        and isinstance(item.get("target_ref"), str)
    }

    core_set = set(core_codes)
    extended_set = set(extended_codes)
    techniques: list[dict[str, object]] = []
    for item in attack_patterns:
        attack_id = extract_attack_id(item)
        stix_id = item.get("id")
        if attack_id is None or not isinstance(stix_id, str):
            continue

        tactic_names = sorted(
            {
                format_attack_tactic(str(phase["phase_name"]))
                for phase in item.get("kill_chain_phases", [])
                if isinstance(phase, dict)
                and phase.get("kill_chain_name") == "mitre-attack"
                and phase.get("phase_name")
            }
        )
        display_group = "core" if attack_id in core_set else "extended"
        if attack_id not in core_set and attack_id in extended_set:
            display_group = "extended"

        techniques.append(
            {
                "code": attack_id,
                "name": str(item.get("name", attack_id)),
                "domain": "enterprise-attack",
                "description": str(item.get("description", "")),
                "attack_url": build_attack_url(attack_id),
                "tactics": tactic_names,
                "platforms": [str(platform) for platform in item.get("x_mitre_platforms", [])],
                "attack_stix_id": stix_id,
                "attack_version": str(item.get("x_mitre_version")) if item.get("x_mitre_version") is not None else None,
                "parent_code": parent_map.get(stix_id),
                "is_subtechnique": bool(item.get("x_mitre_is_subtechnique")),
                "display_group": display_group,
                "revoked": False,
                "deprecated": False,
            }
        )

    return sorted(techniques, key=lambda technique: str(technique["code"]))


def import_attack_techniques_into_session(
    db: object,
    *,
    core_codes: Sequence[str] = (),
    extended_codes: Sequence[str] = (),
    bundle_url: str = DEFAULT_ATTACK_URL,
) -> tuple[int, int]:
    """Download the ATT&CK STIX bundle and upsert all enterprise techniques.

    Uses the provided SQLAlchemy Session directly so it fits into an existing
    transaction/startup flow.  Returns (created, updated) counts.
    Raises on network or HTTP errors — callers should catch if non-fatal.
    """
    import httpx  # deferred — only needed at import time, not module load
    from sqlalchemy import select
    from app.models import Technique

    response = httpx.get(bundle_url, timeout=90.0, follow_redirects=True)
    response.raise_for_status()
    bundle = response.json()
    rows = iter_enterprise_attack_techniques_from_bundle(
        bundle,
        core_codes=core_codes,
        extended_codes=extended_codes,
    )

    existing_by_code: dict[str, object] = {
        row.code: row
        for row in db.scalars(select(Technique)).all()  # type: ignore[union-attr]
    }
    created = 0
    updated = 0
    for payload in rows:
        code = str(payload["code"])
        existing = existing_by_code.get(code)
        if existing is None:
            db.add(Technique(**payload))  # type: ignore[union-attr]
            created += 1
        else:
            for field, value in payload.items():
                setattr(existing, field, value)
            updated += 1

    db.commit()  # type: ignore[union-attr]
    logger.info("ATT&CK import complete: %d created, %d updated", created, updated)
    return created, updated


def build_local_attack_technique(
    *,
    code: str,
    name: str,
    tactic: str,
    display_group: str,
) -> dict[str, object]:
    parent_code = code.split(".", 1)[0] if "." in code else None
    return {
        "code": code,
        "name": name,
        "domain": "enterprise-attack",
        "description": "",
        "attack_url": build_attack_url(code),
        "tactics": [tactic],
        "platforms": [],
        "attack_stix_id": None,
        "attack_version": None,
        "parent_code": parent_code,
        "is_subtechnique": "." in code,
        "display_group": display_group,
        "revoked": False,
        "deprecated": False,
    }
