from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import Capability, Tool, ToolCapability
from app.seed import LEGACY_CAPABILITY_MAP, seed_reference_data


CONTROL_EFFECT_PRIORITY = {"none": 0, "detect": 1, "block": 2, "prevent": 3}
IMPLEMENTATION_LEVEL_PRIORITY = {"none": 0, "partial": 1, "full": 2}


def migrate_legacy_database(database_path: Path) -> None:
    if not database_path.exists():
        return

    with sqlite3.connect(database_path) as connection:
        if not _table_exists(connection, "tool_capabilities"):
            return

        if _schema_is_current(connection):
            return

        legacy_payload = _extract_legacy_payload(connection)

    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db: Session = session_factory()
    try:
        seed_reference_data(db)

        db.add_all(
            Tool(
                id=tool["id"],
                name=tool["name"],
                category=tool["category"],
                tool_types=tool["tool_types"],
                tags=tool["tags"],
            )
            for tool in legacy_payload["tools"]
        )
        db.commit()

        capabilities_by_code = {
            capability.code: capability.id
            for capability in db.query(Capability).all()
        }

        db.add_all(
            ToolCapability(
                tool_id=assignment["tool_id"],
                capability_id=capabilities_by_code[assignment["capability_code"]],
                control_effect=assignment["control_effect"],
                implementation_level=assignment["implementation_level"],
                confidence_source=assignment["confidence_source"],
                confidence_level=assignment["confidence_level"],
            )
            for assignment in legacy_payload["assignments"]
        )
        db.commit()
    finally:
        db.close()
        engine.dispose()


def _schema_is_current(connection: sqlite3.Connection) -> bool:
    required_tables = {
        "capability_assessment_templates",
        "capability_assessment_questions",
        "tool_capability_assessment_answers",
        "tool_capability_evidence",
        "tool_capability_templates",
        "data_sources",
        "tool_data_sources",
        "response_actions",
        "tool_response_actions",
        "capability_required_data_sources",
        "capability_supported_response_actions",
        "capability_configuration_questions",
        "tool_capability_configuration_profiles",
        "tool_capability_configuration_answers",
        "coverage_scopes",
        "tool_capability_scopes",
        "technique_relevant_scopes",
        # BAS assurance validation table (added for BAS classification feature)
        "bas_validations",
    }
    if not required_tables.issubset(_get_table_names(connection)):
        return False

    tool_columns = _get_table_columns(connection, "tools")
    capability_columns = _get_table_columns(connection, "capabilities")
    tool_capability_columns = _get_table_columns(connection, "tool_capabilities")

    return (
        "category" in tool_columns
        and "tool_types" in tool_columns  # JSON array (replaces old tool_type string)
        and "tags" in tool_columns
        and {
            "description",
            "requires_data_sources",
            "supported_by_analytics",
            "supported_by_response",
            "requires_configuration",
            "configuration_profile_type",
        }.issubset(capability_columns)
        and {"id", "control_effect", "confidence_source", "confidence_level"}.issubset(tool_capability_columns)
        and {"optional_tags", "priority"}.issubset(_get_table_columns(connection, "tool_capability_templates"))
        and {"bas_result", "technique_id", "last_validation_date"}.issubset(
            _get_table_columns(connection, "bas_validations")
        )
    )


def _extract_legacy_payload(connection: sqlite3.Connection) -> dict[str, list[dict[str, str | int]]]:
    tool_columns = _get_table_columns(connection, "tools")
    capability_rows = connection.execute("SELECT id, code FROM capabilities").fetchall()
    legacy_capabilities = {capability_id: code for capability_id, code in capability_rows}

    legacy_tools = connection.execute("SELECT id, name FROM tools ORDER BY id").fetchall()
    tools = [
        {
            "id": tool_id,
            "name": name,
            "category": (
                connection.execute("SELECT category FROM tools WHERE id = ?", (tool_id,)).fetchone()[0]
                if "category" in tool_columns
                else "Other"
            ),
            # Migrate old single tool_type string → list.
            # Also handle new tool_types JSON column if already migrated partway.
            "tool_types": (
                [connection.execute("SELECT tool_type FROM tools WHERE id = ?", (tool_id,)).fetchone()[0]]
                if "tool_type" in tool_columns and "tool_types" not in tool_columns
                else (
                    connection.execute("SELECT tool_types FROM tools WHERE id = ?", (tool_id,)).fetchone()[0]
                    if "tool_types" in tool_columns
                    else ["control"]
                )
            ),
            "tags": [],
        }
        for tool_id, name in legacy_tools
    ]

    tool_capability_columns = _get_table_columns(connection, "tool_capabilities")
    select_columns = ["tool_id", "capability_id", "implementation_level"]
    if "control_effect" in tool_capability_columns:
        select_columns.append("control_effect")
    if "confidence_source" in tool_capability_columns:
        select_columns.append("confidence_source")
    if "confidence_level" in tool_capability_columns:
        select_columns.append("confidence_level")

    legacy_assignments = connection.execute(
        f"SELECT {', '.join(select_columns)} FROM tool_capabilities"
    ).fetchall()

    migrated_assignments: dict[tuple[int, str], dict[str, str | int]] = {}
    has_explicit_effect = "control_effect" in tool_capability_columns
    has_confidence_source = "confidence_source" in tool_capability_columns
    has_confidence_level = "confidence_level" in tool_capability_columns

    for row in legacy_assignments:
        row_values = dict(zip(select_columns, row, strict=True))
        tool_id = int(row_values["tool_id"])
        capability_id = int(row_values["capability_id"])
        implementation_level = str(row_values["implementation_level"])

        legacy_code = legacy_capabilities.get(capability_id)
        if legacy_code is None:
            continue

        if has_explicit_effect:
            canonical_code = legacy_code
            control_effect = str(row_values["control_effect"])
        else:
            if legacy_code not in LEGACY_CAPABILITY_MAP:
                continue
            canonical_code, control_effect = LEGACY_CAPABILITY_MAP[legacy_code]

        assignment_key = (tool_id, canonical_code)
        current = migrated_assignments.get(assignment_key)
        confidence_source = (
            str(row_values["confidence_source"])
            if has_confidence_source
            else "declared"
        )
        confidence_level = (
            str(row_values["confidence_level"])
            if has_confidence_level
            else "low"
        )

        if current is None:
            migrated_assignments[assignment_key] = {
                "tool_id": tool_id,
                "capability_code": canonical_code,
                "control_effect": control_effect,
                "implementation_level": implementation_level,
                "confidence_source": confidence_source,
                "confidence_level": confidence_level,
            }
            continue

        if CONTROL_EFFECT_PRIORITY[control_effect] > CONTROL_EFFECT_PRIORITY[str(current["control_effect"])]:
            current["control_effect"] = control_effect

        if (
            IMPLEMENTATION_LEVEL_PRIORITY[implementation_level]
            > IMPLEMENTATION_LEVEL_PRIORITY[str(current["implementation_level"])]
        ):
            current["implementation_level"] = implementation_level

        if confidence_source == "tested" or str(current["confidence_source"]) != "tested":
            current["confidence_source"] = confidence_source

        if confidence_level == "high" or str(current["confidence_level"]) != "high":
            current["confidence_level"] = confidence_level

    return {
        "tools": tools,
        "assignments": list(migrated_assignments.values()),
    }


def _get_table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def _get_table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None
