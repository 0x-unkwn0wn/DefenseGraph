from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import (
    BASValidation,
    Capability,
    CoverageScope,
    DataSource,
    ResponseAction,
    Technique,
    Tool,
    ToolCapability,
    ToolCapabilityAssessmentAnswer,
    ToolCapabilityConfigurationAnswer,
    ToolCapabilityConfigurationProfile,
    ToolCapabilityEvidence,
    ToolCapabilityScope,
    ToolDataSource,
    ToolResponseAction,
)
from app.seed import seed_reference_data, LEGACY_CAPABILITY_MAP


CONTROL_EFFECT_PRIORITY = {"none": 0, "detect": 1, "block": 2, "prevent": 3}
IMPLEMENTATION_LEVEL_PRIORITY = {"none": 0, "partial": 1, "full": 2}


def migrate_legacy_database(database_path: Path) -> Path | None:
    if not database_path.exists():
        return None

    with sqlite3.connect(database_path) as connection:
        if not _table_exists(connection, "tool_capabilities"):
            return None

        if _schema_is_current(connection):
            return None

        legacy_payload = _extract_legacy_payload(connection)

    backup_path = _create_backup(database_path)

    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db: Session = session_factory()
    try:
        seed_reference_data(db)
        _restore_payload(db, legacy_payload)
        db.commit()
    finally:
        db.close()
        engine.dispose()

    return backup_path


def _restore_payload(db: Session, payload: dict[str, list[dict[str, object]]]) -> None:
    db.add_all(
        Tool(
            id=int(tool["id"]),
            name=str(tool["name"]),
            category=str(tool["category"]),
            tool_types=list(tool["tool_types"]),
            tags=list(tool["tags"]),
        )
        for tool in payload["tools"]
    )
    db.flush()

    capabilities_by_code = {capability.code: capability.id for capability in db.query(Capability).all()}
    data_source_ids_by_code = dict(db.execute(select(DataSource.code, DataSource.id)).all())
    response_action_ids_by_code = dict(db.execute(select(ResponseAction.code, ResponseAction.id)).all())
    scope_ids_by_code = dict(db.execute(select(CoverageScope.code, CoverageScope.id)).all())
    technique_ids_by_code = dict(db.execute(select(Technique.code, Technique.id)).all())

    assignment_id_by_key: dict[tuple[int, str], int] = {}
    for assignment in payload["assignments"]:
        capability_code = str(assignment["capability_code"])
        capability_id = capabilities_by_code.get(capability_code)
        if capability_id is None:
            continue
        row = ToolCapability(
            tool_id=int(assignment["tool_id"]),
            capability_id=capability_id,
            control_effect=str(assignment["control_effect"]),
            implementation_level=str(assignment["implementation_level"]),
            confidence_source=str(assignment["confidence_source"]),
            confidence_level=str(assignment["confidence_level"]),
        )
        db.add(row)
        db.flush()
        assignment_id_by_key[(row.tool_id, capability_code)] = row.id

    assessment_question_ids = {
        (capability.code, question.prompt): question.id
        for capability in db.query(Capability).all()
        if capability.assessment_template
        for question in capability.assessment_template.questions
    }
    configuration_question_ids = {
        (capability.code, question.question): question.id
        for capability in db.query(Capability).all()
        for question in capability.configuration_questions
    }

    for answer in payload["assessment_answers"]:
        capability_code = str(answer["capability_code"])
        question_id = assessment_question_ids.get((capability_code, str(answer["question_prompt"])))
        capability_id = capabilities_by_code.get(capability_code)
        if question_id is None or capability_id is None:
            continue
        db.add(
            ToolCapabilityAssessmentAnswer(
                tool_id=int(answer["tool_id"]),
                capability_id=capability_id,
                question_id=question_id,
                answer=str(answer["answer"]),
            )
        )

    for evidence in payload["evidence_items"]:
        capability_code = str(evidence["capability_code"])
        capability_id = capabilities_by_code.get(capability_code)
        if capability_id is None:
            continue
        db.add(
            ToolCapabilityEvidence(
                tool_id=int(evidence["tool_id"]),
                capability_id=capability_id,
                title=str(evidence["title"]),
                evidence_type=str(evidence["evidence_type"]),
                note=str(evidence["note"]),
                file_name=(str(evidence["file_name"]) if evidence["file_name"] is not None else None),
                recorded_at=str(evidence["recorded_at"]),
            )
        )

    for profile in payload["configuration_profiles"]:
        capability_code = str(profile["capability_code"])
        capability_id = capabilities_by_code.get(capability_code)
        if capability_id is None:
            continue
        db.add(
            ToolCapabilityConfigurationProfile(
                tool_id=int(profile["tool_id"]),
                capability_id=capability_id,
                profile_type=(str(profile["profile_type"]) if profile["profile_type"] is not None else None),
                configuration_status=str(profile["configuration_status"]),
                notes=str(profile["notes"]),
                last_updated_at=(str(profile["last_updated_at"]) if profile["last_updated_at"] is not None else None),
            )
        )

    for answer in payload["configuration_answers"]:
        capability_code = str(answer["capability_code"])
        question_id = configuration_question_ids.get((capability_code, str(answer["question_text"])))
        capability_id = capabilities_by_code.get(capability_code)
        if question_id is None or capability_id is None:
            continue
        db.add(
            ToolCapabilityConfigurationAnswer(
                tool_id=int(answer["tool_id"]),
                capability_id=capability_id,
                question_id=question_id,
                answer=str(answer["answer"]),
            )
        )

    for entry in payload["tool_data_sources"]:
        data_source_id = data_source_ids_by_code.get(str(entry["data_source_code"]))
        if data_source_id is None:
            continue
        db.add(
            ToolDataSource(
                tool_id=int(entry["tool_id"]),
                data_source_id=data_source_id,
                ingestion_status=str(entry["ingestion_status"]),
                notes=str(entry["notes"]),
            )
        )

    for entry in payload["tool_response_actions"]:
        response_action_id = response_action_ids_by_code.get(str(entry["response_action_code"]))
        if response_action_id is None:
            continue
        db.add(
            ToolResponseAction(
                tool_id=int(entry["tool_id"]),
                response_action_id=response_action_id,
                implementation_level=str(entry["implementation_level"]),
                notes=str(entry["notes"]),
            )
        )

    for entry in payload["scope_assignments"]:
        assignment_id = assignment_id_by_key.get((int(entry["tool_id"]), str(entry["capability_code"])))
        coverage_scope_id = scope_ids_by_code.get(str(entry["scope_code"]))
        if assignment_id is None or coverage_scope_id is None:
            continue
        db.add(
            ToolCapabilityScope(
                tool_capability_id=assignment_id,
                coverage_scope_id=coverage_scope_id,
                status=str(entry["status"]),
                notes=str(entry["notes"]),
            )
        )

    for row in payload["bas_validations"]:
        technique_id = technique_ids_by_code.get(str(row["technique_code"]))
        if technique_id is None:
            continue
        db.add(
            BASValidation(
                technique_id=technique_id,
                bas_tool_id=(int(row["bas_tool_id"]) if row["bas_tool_id"] is not None else None),
                bas_result=str(row["bas_result"]),
                last_validation_date=(str(row["last_validation_date"]) if row["last_validation_date"] is not None else None),
                notes=str(row["notes"]),
            )
        )


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
        "bas_validations",
    }
    if not required_tables.issubset(_get_table_names(connection)):
        return False

    tool_columns = _get_table_columns(connection, "tools")
    capability_columns = _get_table_columns(connection, "capabilities")
    tool_capability_columns = _get_table_columns(connection, "tool_capabilities")

    return (
        "category" in tool_columns
        and "tool_types" in tool_columns
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
        and {"bas_result", "technique_id", "last_validation_date"}.issubset(_get_table_columns(connection, "bas_validations"))
    )


def _extract_legacy_payload(connection: sqlite3.Connection) -> dict[str, list[dict[str, object]]]:
    capability_rows = connection.execute("SELECT id, code FROM capabilities").fetchall()
    legacy_capabilities = {int(capability_id): str(code) for capability_id, code in capability_rows}
    tool_columns = _get_table_columns(connection, "tools")
    tool_capability_columns = _get_table_columns(connection, "tool_capabilities")

    payload: dict[str, list[dict[str, object]]] = {
        "tools": [],
        "assignments": [],
        "assessment_answers": [],
        "evidence_items": [],
        "tool_data_sources": [],
        "tool_response_actions": [],
        "configuration_profiles": [],
        "configuration_answers": [],
        "scope_assignments": [],
        "bas_validations": [],
    }

    for tool_id, name in connection.execute("SELECT id, name FROM tools ORDER BY id").fetchall():
        category = _fetch_optional_value(connection, "tools", "category", tool_id, "Other")
        tool_types = _extract_tool_types(connection, tool_columns, tool_id)
        tags = _deserialize_json_list(_fetch_optional_value(connection, "tools", "tags", tool_id, []))
        payload["tools"].append(
            {
                "id": int(tool_id),
                "name": str(name),
                "category": str(category or "Other"),
                "tool_types": tool_types or ["control"],
                "tags": tags,
            }
        )

    select_columns = ["tool_id", "capability_id", "implementation_level"]
    if "id" in tool_capability_columns:
        select_columns.insert(0, "id")
    if "control_effect" in tool_capability_columns:
        select_columns.append("control_effect")
    if "confidence_source" in tool_capability_columns:
        select_columns.append("confidence_source")
    if "confidence_level" in tool_capability_columns:
        select_columns.append("confidence_level")

    migrated_assignments: dict[tuple[int, str], dict[str, object]] = {}
    legacy_assignment_key_by_row_id: dict[int, tuple[int, str]] = {}
    has_explicit_effect = "control_effect" in tool_capability_columns

    for row in connection.execute(f"SELECT {', '.join(select_columns)} FROM tool_capabilities").fetchall():
        row_values = dict(zip(select_columns, row, strict=True))
        tool_id = int(row_values["tool_id"])
        legacy_capability_id = int(row_values["capability_id"])
        legacy_code = legacy_capabilities.get(legacy_capability_id)
        if legacy_code is None:
            continue

        capability_code, control_effect = _resolve_capability_code_and_effect(
            legacy_code,
            has_explicit_effect,
            row_values.get("control_effect"),
        )
        if capability_code is None:
            continue

        assignment_key = (tool_id, capability_code)
        if "id" in row_values and row_values["id"] is not None:
            legacy_assignment_key_by_row_id[int(row_values["id"])] = assignment_key

        implementation_level = str(row_values["implementation_level"])
        confidence_source = str(row_values.get("confidence_source") or "declared")
        confidence_level = str(row_values.get("confidence_level") or "low")

        current = migrated_assignments.get(assignment_key)
        if current is None:
            migrated_assignments[assignment_key] = {
                "tool_id": tool_id,
                "capability_code": capability_code,
                "control_effect": control_effect,
                "implementation_level": implementation_level,
                "confidence_source": confidence_source,
                "confidence_level": confidence_level,
            }
            continue

        if CONTROL_EFFECT_PRIORITY[control_effect] > CONTROL_EFFECT_PRIORITY[str(current["control_effect"])]:
            current["control_effect"] = control_effect
        if IMPLEMENTATION_LEVEL_PRIORITY[implementation_level] > IMPLEMENTATION_LEVEL_PRIORITY[str(current["implementation_level"])]:
            current["implementation_level"] = implementation_level
        if _confidence_source_rank(confidence_source) > _confidence_source_rank(str(current["confidence_source"])):
            current["confidence_source"] = confidence_source
        if _confidence_level_rank(confidence_level) > _confidence_level_rank(str(current["confidence_level"])):
            current["confidence_level"] = confidence_level

    payload["assignments"] = list(migrated_assignments.values())

    if _table_exists(connection, "tool_capability_assessment_answers") and _table_exists(connection, "capability_assessment_questions"):
        for tool_id, capability_id, question_prompt, answer in connection.execute(
            """
            SELECT a.tool_id, a.capability_id, q.prompt, a.answer
            FROM tool_capability_assessment_answers a
            JOIN capability_assessment_questions q ON q.id = a.question_id
            """
        ).fetchall():
            capability_code = _resolve_assignment_capability_code(legacy_capabilities, int(capability_id))
            if capability_code is None:
                continue
            payload["assessment_answers"].append(
                {
                    "tool_id": int(tool_id),
                    "capability_code": capability_code,
                    "question_prompt": str(question_prompt),
                    "answer": str(answer),
                }
            )

    if _table_exists(connection, "tool_capability_evidence"):
        for row in connection.execute(
            """
            SELECT tool_id, capability_id, title, evidence_type, note, file_name, recorded_at
            FROM tool_capability_evidence
            """
        ).fetchall():
            capability_code = _resolve_assignment_capability_code(legacy_capabilities, int(row[1]))
            if capability_code is None:
                continue
            payload["evidence_items"].append(
                {
                    "tool_id": int(row[0]),
                    "capability_code": capability_code,
                    "title": str(row[2]),
                    "evidence_type": str(row[3]),
                    "note": str(row[4] or ""),
                    "file_name": row[5],
                    "recorded_at": str(row[6]),
                }
            )

    if _table_exists(connection, "tool_data_sources") and _table_exists(connection, "data_sources"):
        for tool_id, data_source_code, ingestion_status, notes in connection.execute(
            """
            SELECT tds.tool_id, ds.code, tds.ingestion_status, tds.notes
            FROM tool_data_sources tds
            JOIN data_sources ds ON ds.id = tds.data_source_id
            """
        ).fetchall():
            payload["tool_data_sources"].append(
                {
                    "tool_id": int(tool_id),
                    "data_source_code": str(data_source_code),
                    "ingestion_status": str(ingestion_status),
                    "notes": str(notes or ""),
                }
            )

    if _table_exists(connection, "tool_response_actions") and _table_exists(connection, "response_actions"):
        for tool_id, response_action_code, implementation_level, notes in connection.execute(
            """
            SELECT tra.tool_id, ra.code, tra.implementation_level, tra.notes
            FROM tool_response_actions tra
            JOIN response_actions ra ON ra.id = tra.response_action_id
            """
        ).fetchall():
            payload["tool_response_actions"].append(
                {
                    "tool_id": int(tool_id),
                    "response_action_code": str(response_action_code),
                    "implementation_level": str(implementation_level),
                    "notes": str(notes or ""),
                }
            )

    if _table_exists(connection, "tool_capability_configuration_profiles"):
        for row in connection.execute(
            """
            SELECT tool_id, capability_id, profile_type, configuration_status, notes, last_updated_at
            FROM tool_capability_configuration_profiles
            """
        ).fetchall():
            capability_code = _resolve_assignment_capability_code(legacy_capabilities, int(row[1]))
            if capability_code is None:
                continue
            payload["configuration_profiles"].append(
                {
                    "tool_id": int(row[0]),
                    "capability_code": capability_code,
                    "profile_type": row[2],
                    "configuration_status": str(row[3]),
                    "notes": str(row[4] or ""),
                    "last_updated_at": row[5],
                }
            )

    if _table_exists(connection, "tool_capability_configuration_answers") and _table_exists(connection, "capability_configuration_questions"):
        for tool_id, capability_id, question_text, answer in connection.execute(
            """
            SELECT a.tool_id, a.capability_id, q.question, a.answer
            FROM tool_capability_configuration_answers a
            JOIN capability_configuration_questions q ON q.id = a.question_id
            """
        ).fetchall():
            capability_code = _resolve_assignment_capability_code(legacy_capabilities, int(capability_id))
            if capability_code is None:
                continue
            payload["configuration_answers"].append(
                {
                    "tool_id": int(tool_id),
                    "capability_code": capability_code,
                    "question_text": str(question_text),
                    "answer": str(answer),
                }
            )

    if (
        _table_exists(connection, "tool_capability_scopes")
        and _table_exists(connection, "coverage_scopes")
        and "id" in tool_capability_columns
    ):
        for legacy_tool_capability_id, scope_code, status, notes in connection.execute(
            """
            SELECT tcs.tool_capability_id, cs.code, tcs.status, tcs.notes
            FROM tool_capability_scopes tcs
            JOIN coverage_scopes cs ON cs.id = tcs.coverage_scope_id
            """
        ).fetchall():
            assignment_key = legacy_assignment_key_by_row_id.get(int(legacy_tool_capability_id))
            if assignment_key is None:
                continue
            payload["scope_assignments"].append(
                {
                    "tool_id": assignment_key[0],
                    "capability_code": assignment_key[1],
                    "scope_code": str(scope_code),
                    "status": str(status),
                    "notes": str(notes or ""),
                }
            )

    if _table_exists(connection, "bas_validations") and _table_exists(connection, "techniques"):
        for technique_code, bas_tool_id, bas_result, last_validation_date, notes in connection.execute(
            """
            SELECT t.code, b.bas_tool_id, b.bas_result, b.last_validation_date, b.notes
            FROM bas_validations b
            JOIN techniques t ON t.id = b.technique_id
            """
        ).fetchall():
            payload["bas_validations"].append(
                {
                    "technique_code": str(technique_code),
                    "bas_tool_id": bas_tool_id,
                    "bas_result": str(bas_result),
                    "last_validation_date": last_validation_date,
                    "notes": str(notes or ""),
                }
            )

    return payload


def _resolve_assignment_capability_code(legacy_capabilities: dict[int, str], legacy_capability_id: int) -> str | None:
    legacy_code = legacy_capabilities.get(legacy_capability_id)
    if legacy_code is None:
        return None
    capability_code, _ = _resolve_capability_code_and_effect(legacy_code, False, None)
    return capability_code


def _resolve_capability_code_and_effect(
    legacy_code: str,
    has_explicit_effect: bool,
    explicit_effect: object,
) -> tuple[str | None, str]:
    if has_explicit_effect:
        return legacy_code, str(explicit_effect)
    if legacy_code not in LEGACY_CAPABILITY_MAP:
        return None, "none"
    return LEGACY_CAPABILITY_MAP[legacy_code]


def _extract_tool_types(connection: sqlite3.Connection, tool_columns: set[str], tool_id: int) -> list[str]:
    if "tool_types" in tool_columns:
        raw_value = _fetch_optional_value(connection, "tools", "tool_types", tool_id, ["control"])
        return _deserialize_json_list(raw_value) or ["control"]
    if "tool_type" in tool_columns:
        raw_value = _fetch_optional_value(connection, "tools", "tool_type", tool_id, "control")
        return [str(raw_value or "control")]
    return ["control"]


def _deserialize_json_list(raw_value: object) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if not stripped:
            return []
        try:
            decoded = json.loads(stripped)
            if isinstance(decoded, list):
                return [str(item) for item in decoded if str(item).strip()]
        except json.JSONDecodeError:
            return [stripped]
    return [str(raw_value)]


def _fetch_optional_value(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    row_id: int,
    default: object,
) -> object:
    if column_name not in _get_table_columns(connection, table_name):
        return default
    row = connection.execute(
        f"SELECT {column_name} FROM {table_name} WHERE id = ?",
        (row_id,),
    ).fetchone()
    if row is None:
        return default
    return row[0]


def _create_backup(database_path: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    backup_path = database_path.with_name(f"{database_path.stem}.pre_migration_{timestamp}{database_path.suffix}")
    shutil.copy2(database_path, backup_path)
    return backup_path


def _confidence_source_rank(value: str) -> int:
    return {"declared": 0, "assessed": 1, "evidenced": 2, "tested": 3}.get(value, 0)


def _confidence_level_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(value, 0)


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
