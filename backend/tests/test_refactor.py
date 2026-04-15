import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base
from app.main import app
import app.main as main_module
from app.migration import migrate_legacy_database
from app.models import CapabilityTechniqueMap, Technique
from app.seed import (
    ATTACK_TECHNIQUE_CATALOG,
    CAPABILITY_TECHNIQUE_MAPS,
    CORE_TECHNIQUE_CODES,
    EXTENDED_TECHNIQUE_CODES,
    TECHNIQUES,
    seed_reference_data,
    validate_attack_catalog,
)


class DefenseGraphConfidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp_dir.name) / "test.db"
        cls.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False},
        )
        cls.session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.engine,
        )
        cls.original_engine = main_module.engine
        cls.original_session_local = main_module.SessionLocal
        cls.original_migrate = main_module.migrate_legacy_database

        main_module.engine = cls.engine
        main_module.SessionLocal = cls.session_local
        main_module.migrate_legacy_database = lambda _: None

    @classmethod
    def tearDownClass(cls):
        main_module.engine = cls.original_engine
        main_module.SessionLocal = cls.original_session_local
        main_module.migrate_legacy_database = cls.original_migrate
        cls.engine.dispose()
        try:
            cls.temp_dir.cleanup()
        except PermissionError:
            pass

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)

    def _create_tool(self, name: str, category: str = "Other", tool_type: str | None = None) -> dict:
        resolved_tool_type = (
            tool_type
            or (
                "analytics"
                if "Security Analytics" in category
                else "response" if "SOAR" in category else "control"
            )
        )
        response = self.client.post(
            "/tools",
            json={"name": name, "category": category, "tool_types": [resolved_tool_type], "tags": []},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def _find_capability(self, code: str) -> dict:
        capability_rows = self.client.get("/capabilities").json()
        return next(item for item in capability_rows if item["code"] == code)

    def _assign_capability(
        self,
        tool_id: int,
        capability_id: int,
        control_effect: str,
        implementation_level: str,
    ) -> dict:
        response = self.client.post(
            f"/tools/{tool_id}/capabilities",
            json={
                "capability_id": capability_id,
                "control_effect_default": control_effect,
                "implementation_level": implementation_level,
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _find_data_source(self, code: str) -> dict:
        rows = self.client.get("/data-sources").json()
        return next(item for item in rows if item["code"] == code)

    def _find_response_action(self, code: str) -> dict:
        rows = self.client.get("/response-actions").json()
        return next(item for item in rows if item["code"] == code)

    def _find_scope(self, code: str) -> dict:
        rows = self.client.get("/coverage-scopes").json()
        return next(item for item in rows if item["code"] == code)

    def _set_scopes(
        self,
        tool_id: int,
        capability_id: int,
        scope_entries: list[tuple[str, str, str]],
    ) -> dict:
        payload = {
            "scopes": [
                {
                    "coverage_scope_id": self._find_scope(scope_code)["id"],
                    "status": status,
                    "notes": notes,
                }
                for scope_code, status, notes in scope_entries
            ]
        }
        response = self.client.post(
            f"/tools/{tool_id}/capabilities/{capability_id}/scopes",
            json=payload,
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _set_technique_overrides(
        self,
        tool_id: int,
        capability_id: int,
        override_entries: list[tuple[str, str, str | None, str]],
    ) -> dict:
        technique_rows = self.client.get("/coverage").json()
        technique_id_by_code = {
            row["technique_code"]: row["technique_id"]
            for row in technique_rows
        }
        payload = {
            "overrides": [
                {
                    "technique_id": technique_id_by_code[technique_code],
                    "control_effect_override": control_effect_override,
                    "implementation_level_override": implementation_level_override,
                    "notes": notes,
                }
                for technique_code, control_effect_override, implementation_level_override, notes in override_entries
            ]
        }
        response = self.client.post(
            f"/tools/{tool_id}/capabilities/{capability_id}/technique-overrides",
            json=payload,
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _verify_configuration(
        self,
        tool_id: int,
        capability_id: int,
        answers: list[str],
        notes: str = "",
    ) -> dict:
        profile_response = self.client.post(
            f"/tools/{tool_id}/capabilities/{capability_id}/configuration-profile",
            json={"notes": notes},
        )
        self.assertEqual(profile_response.status_code, 200)
        questions = profile_response.json()["configuration_questions"]
        submission = {
            "answers": [
                {"question_id": question["id"], "answer": answer}
                for question, answer in zip(questions, answers, strict=False)
            ]
        }
        answer_response = self.client.post(
            f"/tools/{tool_id}/capabilities/{capability_id}/configuration-answers",
            json=submission,
        )
        self.assertEqual(answer_response.status_code, 200)
        return answer_response.json()

    def _coverage_row(self, technique_code: str) -> dict:
        return next(item for item in self.client.get("/coverage").json() if item["technique_code"] == technique_code)

    def _mapping_effects_for(self, capability_id: int, technique_code: str) -> list[str]:
        with self.session_local() as db:
            rows = db.execute(
                select(CapabilityTechniqueMap.control_effect)
                .join(Technique, Technique.id == CapabilityTechniqueMap.technique_id)
                .where(
                    CapabilityTechniqueMap.capability_id == capability_id,
                    Technique.code == technique_code,
                )
            ).scalars().all()

        return sorted(set(rows))

    def test_tool_capability_defaults_to_declared_low_confidence(self):
        tool = self._create_tool("Email Security", "Email")
        capability = self._find_capability("CAP-004")
        response = self._assign_capability(tool["id"], capability["id"], "prevent", "full")

        assignment = next(
            item
            for item in response["capabilities"]
            if item["capability_id"] == capability["id"]
        )
        self.assertEqual(assignment["confidence_source"], "declared")
        self.assertEqual(assignment["confidence_level"], "low")
        self.assertEqual(assignment["control_effect_default"], "prevent")

    def test_unmapped_technique_is_not_counted_as_gap(self):
        with self.session_local() as db:
            db.add(Technique(code="T9000", name="Unmapped Technique"))
            db.commit()

        row = self._coverage_row("T9000")

        self.assertFalse(row["has_capability_mappings"])
        self.assertEqual(row["mapped_capability_count"], 0)
        self.assertEqual(row["coverage_status"], "unmapped")
        self.assertFalse(row["is_gap_no_coverage"])
        self.assertFalse(row["is_gap_scope_missing"])
        self.assertEqual(
            row["dependency_flags"],
            ["No capability mappings defined for this technique"],
        )

    def test_requires_configuration_without_profile_stays_low_and_unconfigured(self):
        tool = self._create_tool("Cloud Edge", "Other")
        capability = self._find_capability("CAP-031")
        self._assign_capability(tool["id"], capability["id"], "prevent", "full")

        detail = self.client.get(f"/tools/{tool['id']}/capabilities/{capability['id']}").json()
        self.assertEqual(detail["confidence"]["confidence_level"], "low")
        self.assertEqual(detail["configuration_summary"]["configuration_status"], "unknown")

        row = next(
            item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1190"
        )
        self.assertTrue(row["is_gap_unconfigured_control"])

    def test_configuration_not_enabled_removes_effective_contribution(self):
        tool = self._create_tool("Cloud Edge Disabled", "Other")
        capability = self._find_capability("CAP-031")
        self._assign_capability(tool["id"], capability["id"], "prevent", "full")
        self._set_scopes(tool["id"], capability["id"], [("public_facing_app", "full", "Internet-facing apps only")])
        self._verify_configuration(tool["id"], capability["id"], ["no", "no", "no", "no"])

        row = next(
            item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1190"
        )
        self.assertEqual(row["effective_control_effect"], "none")
        self.assertTrue(row["is_gap_unconfigured_control"])

    def test_configuration_partially_enabled_degrades_to_partial_gap(self):
        tool = self._create_tool("Segmented Network", "Other")
        capability = self._find_capability("CAP-032")
        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(tool["id"], capability["id"], [("server", "full", "Server VLANs enforced")])
        detail = self._verify_configuration(tool["id"], capability["id"], ["yes", "partial", "no"])

        self.assertEqual(detail["configuration_summary"]["configuration_status"], "partially_enabled")
        self.assertEqual(detail["confidence"]["confidence_level"], "low")

        row = next(
            item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1021"
        )
        self.assertEqual(row["effective_control_effect"], "block")
        self.assertTrue(row["is_gap_partial"])
        self.assertTrue(row["is_gap_partially_configured_control"])

    def test_configuration_enabled_contributes_normally(self):
        tool = self._create_tool("F5 WAF", "Other")
        capability = self._find_capability("CAP-031")
        self._assign_capability(tool["id"], capability["id"], "prevent", "full")
        self._set_scopes(tool["id"], capability["id"], [("public_facing_app", "full", "WAF applied to all apps")])
        detail = self._verify_configuration(tool["id"], capability["id"], ["yes", "yes", "yes", "yes"])

        self.assertEqual(detail["configuration_summary"]["configuration_status"], "enabled")

        row = next(
            item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1190"
        )
        self.assertEqual(row["effective_control_effect"], "prevent")
        self.assertFalse(row["is_gap_unconfigured_control"])
        self.assertFalse(row["is_gap_partially_configured_control"])

    def test_confidence_transitions_from_declared_to_assessed_to_evidenced(self):
        tool = self._create_tool("Identity Monitor", "Identity")
        capability = self._find_capability("CAP-009")
        self._assign_capability(tool["id"], capability["id"], "detect", "full")

        initial_detail = self.client.get(f"/tools/{tool['id']}/capabilities/{capability['id']}")
        self.assertEqual(initial_detail.status_code, 200)
        self.assertEqual(initial_detail.json()["confidence"]["confidence_source"], "declared")
        self.assertEqual(initial_detail.json()["confidence"]["confidence_level"], "low")

        template = self.client.get(f"/capabilities/{capability['id']}/assessment-template").json()
        answers_payload = {
            "answers": [
                {"question_id": question["id"], "answer": "yes"}
                for question in template["questions"][:3]
            ]
            + [{"question_id": template["questions"][3]["id"], "answer": "partial"}]
        }
        assessed_detail = self.client.post(
            f"/tools/{tool['id']}/capabilities/{capability['id']}/assessment-answers",
            json=answers_payload,
        )
        self.assertEqual(assessed_detail.status_code, 200)
        self.assertEqual(assessed_detail.json()["confidence"]["confidence_source"], "assessed")
        self.assertEqual(assessed_detail.json()["confidence"]["confidence_level"], "high")

        evidenced_detail = self.client.post(
            f"/tools/{tool['id']}/capabilities/{capability['id']}/evidence",
            json={
                "title": "Gateway policy export",
                "evidence_type": "config",
                "note": "Identity monitoring rules enabled",
                "file_name": "policy-export.json",
                "recorded_at": "2026-04-13",
            },
        )
        self.assertEqual(evidenced_detail.status_code, 200)
        self.assertEqual(evidenced_detail.json()["confidence"]["confidence_source"], "evidenced")
        self.assertEqual(evidenced_detail.json()["confidence"]["evidence_count"], 1)

    def test_coverage_returns_new_gap_flags_and_confidence(self):
        tool = self._create_tool("DNS Resolver", "DNS")
        capability = self._find_capability("CAP-006")
        self._assign_capability(tool["id"], capability["id"], "detect", "full")
        self._set_scopes(tool["id"], capability["id"], [("endpoint_user_device", "full", "Managed endpoints resolve through DNS control")])

        dns_row = next(
            item
            for item in self.client.get("/coverage").json()
            if item["technique_code"] == "T1071.004"
        )
        self.assertEqual(dns_row["effective_control_effect"], "detect")
        self.assertEqual(dns_row["coverage_status"], "detect_only")
        self.assertTrue(dns_row["is_gap_detect_only"])
        self.assertTrue(dns_row["is_gap_low_confidence"])
        self.assertTrue(dns_row["is_gap_single_tool_dependency"])

    def test_coverage_marks_partial_when_effective_path_is_partial(self):
        tool = self._create_tool("Remote Access Control", "SASE")
        capability = self._find_capability("CAP-012")
        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(tool["id"], capability["id"], [("server", "partial", "Server remote access partially enforced")])

        remote_services_row = next(
            item
            for item in self.client.get("/coverage").json()
            if item["technique_code"] == "T1021"
        )
        self.assertEqual(remote_services_row["effective_control_effect"], "block")
        self.assertEqual(remote_services_row["coverage_status"], "partial")
        self.assertTrue(remote_services_row["is_gap_partial"])

    def test_analytics_tool_without_required_data_sources_does_not_claim_coverage(self):
        tool = self._create_tool("QRadar", "Security Analytics", "analytics")
        capability = self._find_capability("CAP-009")
        self._assign_capability(tool["id"], capability["id"], "detect", "full")
        self._set_scopes(tool["id"], capability["id"], [("identity", "full", "Identity analytics use case")])

        row = next(
            item
            for item in self.client.get("/coverage").json()
            if item["technique_code"] == "T1078"
        )
        self.assertEqual(row["effective_control_effect"], "none")
        self.assertTrue(row["is_gap_missing_data_sources"])

    def test_analytics_tool_with_required_data_sources_contributes_detect_coverage(self):
        tool = self._create_tool("QRadar", "Security Analytics", "analytics")
        capability = self._find_capability("CAP-009")
        data_source = self._find_data_source("DS-001")
        endpoint_data = self._find_data_source("DS-002")
        self.client.post(
            f"/tools/{tool['id']}/data-sources",
            json={"data_source_id": data_source["id"], "ingestion_status": "full", "notes": ""},
        )
        self.client.post(
            f"/tools/{tool['id']}/data-sources",
            json={"data_source_id": endpoint_data["id"], "ingestion_status": "full", "notes": ""},
        )
        self._assign_capability(tool["id"], capability["id"], "detect", "full")
        self._set_scopes(tool["id"], capability["id"], [("identity", "full", "Identity controls covered")])

        row = next(
            item
            for item in self.client.get("/coverage").json()
            if item["technique_code"] == "T1078"
        )
        self.assertEqual(row["effective_control_effect"], "detect")
        self.assertFalse(row["is_gap_missing_data_sources"])
        self.assertTrue(any("analytics" in item["tool_types"] for item in row["contributing_tools"]))

    def test_response_tool_without_upstream_detection_does_not_create_coverage(self):
        tool = self._create_tool("XSOAR", "SOAR", "response")
        action = self._find_response_action("RA-002")
        self.client.post(
            f"/tools/{tool['id']}/response-actions",
            json={"response_action_id": action["id"], "implementation_level": "full", "notes": ""},
        )

        row = next(
            item
            for item in self.client.get("/coverage").json()
            if item["technique_code"] == "T1078"
        )
        self.assertEqual(row["effective_control_effect"], "none")
        self.assertTrue(row["is_gap_response_without_detection"])

    def test_detection_plus_response_marks_response_enabled(self):
        detect_tool = self._create_tool("Identity Analytics", "Security Analytics", "analytics")
        capability = self._find_capability("CAP-009")
        ad_logs = self._find_data_source("DS-001")
        self.client.post(
            f"/tools/{detect_tool['id']}/data-sources",
            json={"data_source_id": ad_logs["id"], "ingestion_status": "full", "notes": ""},
        )
        self._assign_capability(detect_tool["id"], capability["id"], "detect", "full")
        self._set_scopes(detect_tool["id"], capability["id"], [("identity", "full", "Identity telemetry path")])

        response_tool = self._create_tool("XSOAR", "SOAR", "response")
        action = self._find_response_action("RA-002")
        self.client.post(
            f"/tools/{response_tool['id']}/response-actions",
            json={"response_action_id": action["id"], "implementation_level": "full", "notes": ""},
        )

        row = next(
            item
            for item in self.client.get("/coverage").json()
            if item["technique_code"] == "T1078"
        )
        self.assertEqual(row["effective_control_effect"], "detect")
        self.assertEqual(row["effective_outcome"], "detect_with_response")
        self.assertTrue(row["response_enabled"])
        self.assertTrue(any(action_row["tool_name"] == "XSOAR" for action_row in row["response_actions"]))

    def test_curated_attack_subset_contains_exactly_thirty_five_mapped_techniques(self):
        seeded_codes = [technique["code"] for technique in TECHNIQUES]
        self.assertEqual(len(seeded_codes), 35)
        self.assertEqual(len(set(seeded_codes)), 35)

        with self.session_local() as db:
            technique_codes = db.scalars(select(Technique.code).order_by(Technique.code)).all()
            mapped_codes = {
                code
                for (code,) in db.execute(
                    select(Technique.code)
                    .join(CapabilityTechniqueMap, CapabilityTechniqueMap.technique_id == Technique.id)
                    .distinct()
                ).all()
            }

        self.assertEqual(len(technique_codes), 35)
        self.assertEqual(set(technique_codes), set(seeded_codes))
        self.assertEqual(mapped_codes, set(seeded_codes))
        self.assertEqual(
            {technique_code for _, technique_code, _, _ in CAPABILITY_TECHNIQUE_MAPS},
            set(seeded_codes),
        )
        self.assertEqual(len(CORE_TECHNIQUE_CODES), 20)
        self.assertEqual(len(EXTENDED_TECHNIQUE_CODES), 15)

    def test_attack_catalog_validation_rejects_duplicate_technique_ids(self):
        invalid_catalog = [
            *ATTACK_TECHNIQUE_CATALOG,
            ATTACK_TECHNIQUE_CATALOG[0],
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate ATT&CK technique IDs"):
            validate_attack_catalog(invalid_catalog, CORE_TECHNIQUE_CODES, EXTENDED_TECHNIQUE_CODES, CAPABILITY_TECHNIQUE_MAPS)

    def test_attack_catalog_validation_rejects_missing_tactics(self):
        invalid_catalog = [
            {
                **ATTACK_TECHNIQUE_CATALOG[0],
                "tactic": "",
            },
            *ATTACK_TECHNIQUE_CATALOG[1:],
        ]
        with self.assertRaisesRegex(ValueError, "missing tactic assignments"):
            validate_attack_catalog(invalid_catalog, CORE_TECHNIQUE_CODES, EXTENDED_TECHNIQUE_CODES, CAPABILITY_TECHNIQUE_MAPS)

    def test_attack_catalog_validation_rejects_unmapped_techniques(self):
        invalid_maps = [
            entry
            for entry in CAPABILITY_TECHNIQUE_MAPS
            if entry[1] != "T1190"
        ]
        with self.assertRaisesRegex(ValueError, "missing capability mappings"):
            validate_attack_catalog(ATTACK_TECHNIQUE_CATALOG, CORE_TECHNIQUE_CODES, EXTENDED_TECHNIQUE_CODES, invalid_maps)

    def test_attack_catalog_validation_rejects_core_extended_overlap_and_wrong_counts(self):
        overlapping_extended = [CORE_TECHNIQUE_CODES[0], *EXTENDED_TECHNIQUE_CODES[1:]]
        with self.assertRaisesRegex(ValueError, "both Core and Extended"):
            validate_attack_catalog(ATTACK_TECHNIQUE_CATALOG, CORE_TECHNIQUE_CODES, overlapping_extended, CAPABILITY_TECHNIQUE_MAPS)

        short_core = CORE_TECHNIQUE_CODES[:-1]
        with self.assertRaisesRegex(ValueError, "exactly 20 unique techniques"):
            validate_attack_catalog(ATTACK_TECHNIQUE_CATALOG, short_core, EXTENDED_TECHNIQUE_CODES, CAPABILITY_TECHNIQUE_MAPS)

    def test_named_capability_mapping_patches_are_present_and_idempotent(self):
        capabilities = self.client.get("/capabilities")
        self.assertEqual(capabilities.status_code, 200)
        capability_rows = {item["name"]: item for item in capabilities.json()}

        remote_access = capability_rows["Remote Access Abuse Detection"]
        remote_codes = {item["technique_code"] for item in remote_access["related_techniques"]}
        self.assertTrue({"T1078", "T1021", "T1133", "T1087", "T1110"}.issubset(remote_codes))

        host_isolation = capability_rows["Host Isolation Automation"]
        host_isolation_codes = {item["technique_code"] for item in host_isolation["related_techniques"]}
        self.assertTrue({"T1021", "T1105", "T1071", "T1041", "T1570"}.issubset(host_isolation_codes))

        account_disable = capability_rows["Account Disable Automation"]
        account_disable_codes = {item["technique_code"] for item in account_disable["related_techniques"]}
        self.assertTrue({"T1078", "T1136", "T1098", "T1110", "T1003"}.issubset(account_disable_codes))

        with self.session_local() as db:
            before_count = db.query(CapabilityTechniqueMap).count()
            from app.seed import _apply_named_capability_mapping_patches

            _apply_named_capability_mapping_patches(db)
            after_count = db.query(CapabilityTechniqueMap).count()

        self.assertEqual(before_count, after_count)

    def test_tags_endpoint_returns_seeded_tag_catalog(self):
        response = self.client.get("/tags")
        self.assertEqual(response.status_code, 200)
        tag_names = [item["name"] for item in response.json()]
        self.assertIn("Active Directory", tag_names)
        self.assertIn("Password Security", tag_names)

    def test_templates_endpoint_returns_core_and_optional_templates_for_pure_edr(self):
        response = self.client.get("/templates?category=EDR")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        capability_codes = [item["capability"]["code"] for item in payload]

        self.assertIn("CAP-001", capability_codes)
        self.assertIn("CAP-003", capability_codes)
        self.assertIn("CAP-013", capability_codes)
        self.assertTrue(any(item["suggestion_group"] == "core" for item in payload))
        self.assertTrue(any(item["suggestion_group"] == "optional" for item in payload))

    def test_specops_like_suggestions_adapt_to_identity_and_password_tags(self):
        response = self.client.get(
            "/templates?category=Identity&tags=Active%20Directory&tags=Password%20Security"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        capability_codes = [item["capability"]["code"] for item in payload]

        self.assertIn("CAP-009", capability_codes)
        self.assertIn("CAP-008", capability_codes)
        self.assertIn("CAP-021", capability_codes)
        self.assertIn("CAP-022", capability_codes)
        self.assertIn("CAP-023", capability_codes)
        self.assertIn("CAP-024", capability_codes)
        self.assertTrue(
            any(item["capability"]["code"] == "CAP-024" and item["suggestion_group"] == "core" for item in payload)
        )
        self.assertTrue(
            any(
                item["capability"]["code"] == "CAP-021" and "Active Directory" in item["matched_tags"]
                for item in payload
            )
        )

    def test_mixed_sase_suggestions_use_tags_without_returning_empty_results(self):
        response = self.client.get(
            "/templates?category=SASE&tags=Network%20Traffic&tags=Data%20Loss%20Prevention&tags=Authentication"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        capability_codes = [item["capability"]["code"] for item in payload]

        self.assertGreater(len(payload), 0)
        self.assertIn("CAP-006", capability_codes)
        self.assertIn("CAP-007", capability_codes)
        self.assertIn("CAP-009", capability_codes)

    def test_apply_templates_to_tool_assigns_selected_capabilities(self):
        tool = self._create_tool("Endpoint Control", "EDR")
        templates = self.client.get("/templates?category=EDR").json()
        selected = [
            {
                "template_id": templates[0]["id"],
                "control_effect": templates[0]["default_effect"],
                "implementation_level": templates[0]["default_implementation_level"],
            },
            {
                "template_id": templates[1]["id"],
                "control_effect": "block",
                "implementation_level": templates[1]["default_implementation_level"],
            },
        ]

        response = self.client.post(
            f"/tools/{tool['id']}/templates",
            json={"selected_templates": selected},
        )
        self.assertEqual(response.status_code, 200)
        assignments = response.json()["capabilities"]

        self.assertEqual(len(assignments), 2)
        self.assertTrue(any(item["control_effect_default"] == "block" for item in assignments))

    def test_default_effect_applies_to_all_related_techniques_without_overrides(self):
        tool = self._create_tool("Override Default Isolation", "EDR")
        capability = self._find_capability("CAP-028")
        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(
            tool["id"],
            capability["id"],
            [
                ("endpoint_user_device", "full", "Endpoints"),
                ("server", "full", "Servers"),
                ("cloud_workload", "full", "Cloud"),
            ],
        )

        coverage_rows = self.client.get("/coverage").json()
        for technique_code in ("T1021", "T1041", "T1570"):
            row = next(item for item in coverage_rows if item["technique_code"] == technique_code)
            self.assertEqual(row["best_effect"], "block")
            self.assertEqual(row["available_effects"], ["block"])
            self.assertEqual(row["blocking_count"], 1)

    def test_single_technique_override_changes_only_that_technique(self):
        tool = self._create_tool("Selective Edge Control", "SASE")
        capability = self._find_capability("CAP-025")
        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(
            tool["id"],
            capability["id"],
            [
                ("identity", "full", "Identity-aware remote access"),
                ("public_facing_app", "full", "Internet-facing edge"),
                ("server", "full", "Server workloads"),
            ],
        )
        self._verify_configuration(tool["id"], capability["id"], ["yes"] * 10)
        detail = self._set_technique_overrides(
            tool["id"],
            capability["id"],
            [("T1133", "detect", None, "Remote services are only monitored")],
        )

        self.assertEqual(len(detail["technique_overrides"]), 1)
        self.assertEqual(detail["technique_overrides"][0]["technique_code"], "T1133")
        self.assertEqual(detail["technique_overrides"][0]["control_effect_override"], "detect")

        coverage_rows = self.client.get("/coverage").json()
        remote_row = next(item for item in coverage_rows if item["technique_code"] == "T1133")
        exploit_row = next(item for item in coverage_rows if item["technique_code"] == "T1190")
        self.assertEqual(remote_row["best_effect"], "detect")
        self.assertEqual(remote_row["available_effects"], ["detect"])
        self.assertEqual(exploit_row["best_effect"], "block")

    def test_override_downgrade_changes_multi_tool_aggregation(self):
        tool_a = self._create_tool("Policy Edge Control", "SASE")
        tool_b = self._create_tool("Remote Access Monitor", "Identity")
        capability_a = self._find_capability("CAP-025")
        capability_b = self._find_capability("CAP-030")

        self._assign_capability(tool_a["id"], capability_a["id"], "block", "full")
        self._set_scopes(
            tool_a["id"],
            capability_a["id"],
            [
                ("identity", "full", "Identity"),
                ("public_facing_app", "full", "Internet edge"),
                ("server", "full", "Servers"),
            ],
        )
        self._verify_configuration(tool_a["id"], capability_a["id"], ["yes"] * 10)
        self._set_technique_overrides(
            tool_a["id"],
            capability_a["id"],
            [("T1133", "detect", None, "Remote services are monitored, not blocked")],
        )

        self._assign_capability(tool_b["id"], capability_b["id"], "detect", "full")
        self._set_scopes(
            tool_b["id"],
            capability_b["id"],
            [
                ("identity", "full", "Identity"),
                ("public_facing_app", "full", "Internet edge"),
            ],
        )

        row = next(item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1133")
        self.assertEqual(row["available_effects"], ["detect"])
        self.assertEqual(row["best_effect"], "detect")
        self.assertEqual(row["detection_count"], 2)

    def test_prevent_still_wins_after_overrides_are_resolved(self):
        tool_a = self._create_tool("Policy DLP 2", "DLP")
        tool_b = self._create_tool("Suite DLP", "DLP")
        capability_a = self._find_capability("CAP-104")
        capability_b = self._find_capability("CAP-105")

        self._assign_capability(tool_a["id"], capability_a["id"], "block", "full")
        self._set_scopes(tool_a["id"], capability_a["id"], [("saas", "full", "SaaS only")])
        self._set_technique_overrides(
            tool_a["id"],
            capability_a["id"],
            [("T1567", "detect", None, "Only alert for sanctioned SaaS")],
        )

        self._assign_capability(tool_b["id"], capability_b["id"], "prevent", "full")
        self._set_scopes(tool_b["id"], capability_b["id"], [("saas", "full", "SaaS enforcement")])
        self._verify_configuration(tool_b["id"], capability_b["id"], ["yes", "yes", "yes"])

        row = next(item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1567")
        self.assertEqual(row["available_effects"], ["prevent", "detect"])
        self.assertEqual(row["best_effect"], "prevent")
        self.assertEqual(row["prevention_count"], 1)

    def test_structural_mapping_allows_default_block_without_clipping(self):
        tool = self._create_tool("Structural Block Control", "Identity")
        capability = self._find_capability("CAP-028")

        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(
            tool["id"],
            capability["id"],
            [
                ("endpoint_user_device", "full", "Endpoints"),
                ("server", "full", "Servers"),
                ("cloud_workload", "full", "Cloud"),
            ],
        )

        row = self._coverage_row("T1041")
        self.assertEqual(row["best_effect"], "block")
        self.assertEqual(row["available_effects"], ["block"])

    def test_structural_mapping_uses_override_detect_without_clipping(self):
        tool = self._create_tool("Structural Override Control", "Identity")
        capability = self._find_capability("CAP-028")

        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(
            tool["id"],
            capability["id"],
            [
                ("endpoint_user_device", "full", "Endpoints"),
                ("server", "full", "Servers"),
                ("cloud_workload", "full", "Cloud"),
            ],
        )
        self._set_technique_overrides(
            tool["id"],
            capability["id"],
            [("T1041", "detect", None, "This technique is alert-only")],
        )

        row = self._coverage_row("T1041")
        self.assertEqual(row["best_effect"], "detect")
        self.assertEqual(row["available_effects"], ["detect"])

    def test_detect_only_historical_mapping_does_not_clip_prevent_override(self):
        tool = self._create_tool("Authoritative Override Control", "Identity")
        capability = self._find_capability("CAP-030")

        self.assertEqual(self._mapping_effects_for(capability["id"], "T1133"), ["detect"])

        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(
            tool["id"],
            capability["id"],
            [
                ("identity", "full", "Identity coverage"),
                ("public_facing_app", "full", "External access points"),
            ],
        )
        self._set_technique_overrides(
            tool["id"],
            capability["id"],
            [("T1133", "prevent", None, "This deployment actively prevents remote access abuse")],
        )

        row = self._coverage_row("T1133")
        self.assertEqual(row["best_effect"], "prevent")
        self.assertEqual(row["available_effects"], ["prevent"])
        self.assertEqual(row["prevention_count"], 1)

    def test_prevent_only_historical_mapping_does_not_null_detect_override(self):
        tool = self._create_tool("Prevent Legacy Mapping Control", "Identity")
        capability = self._find_capability("CAP-024")

        self.assertEqual(self._mapping_effects_for(capability["id"], "T1110"), ["prevent"])

        self._assign_capability(tool["id"], capability["id"], "prevent", "full")
        self._set_scopes(tool["id"], capability["id"], [("identity", "full", "Identity systems")])
        self._set_technique_overrides(
            tool["id"],
            capability["id"],
            [("T1110", "detect", None, "This deployment only alerts on password attacks")],
        )

        row = self._coverage_row("T1110")
        self.assertEqual(row["best_effect"], "detect")
        self.assertEqual(row["available_effects"], ["detect"])
        self.assertEqual(row["detection_count"], 1)

    def test_tool_does_not_contribute_without_structural_mapping(self):
        tool = self._create_tool("Unmapped Capability Control", "Identity")
        capability = self._find_capability("CAP-009")

        self._assign_capability(tool["id"], capability["id"], "prevent", "full")
        self._set_scopes(tool["id"], capability["id"], [("identity", "full", "Identity systems")])

        row = self._coverage_row("T1190")
        self.assertEqual(row["best_effect"], "none")
        self.assertEqual(row["available_effects"], [])
        self.assertEqual(row["tool_count"], 0)

    def test_multiple_tools_aggregate_resolved_effects_without_mapping_caps(self):
        detect_tool = self._create_tool("Detect Identity Control", "Identity")
        block_tool = self._create_tool("Block Identity Control", "Identity")
        prevent_tool = self._create_tool("Prevent Identity Control", "Identity")

        detect_capability = self._find_capability("CAP-030")
        block_capability = self._find_capability("CAP-027")
        prevent_capability = self._find_capability("CAP-024")

        self._assign_capability(detect_tool["id"], detect_capability["id"], "detect", "full")
        self._set_scopes(detect_tool["id"], detect_capability["id"], [("identity", "full", "Identity systems")])

        self._assign_capability(block_tool["id"], block_capability["id"], "block", "full")
        self._set_scopes(block_tool["id"], block_capability["id"], [("identity", "full", "Identity systems")])

        self._assign_capability(prevent_tool["id"], prevent_capability["id"], "prevent", "full")
        self._set_scopes(prevent_tool["id"], prevent_capability["id"], [("identity", "full", "Identity systems")])

        row = self._coverage_row("T1110")
        self.assertEqual(row["available_effects"], ["prevent", "block", "detect"])
        self.assertEqual(row["best_effect"], "prevent")
        self.assertEqual(row["detection_count"], 1)
        self.assertEqual(row["blocking_count"], 1)
        self.assertEqual(row["prevention_count"], 1)

    def test_scope_endpoint_only_marks_multi_scope_technique_as_partial(self):
        tool = self._create_tool("Endpoint DLP", "DLP")
        capability = self._find_capability("CAP-007")
        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(tool["id"], capability["id"], [("endpoint_user_device", "full", "Endpoint agents only")])

        row = next(item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1041")
        self.assertEqual(row["effective_control_effect"], "block")
        self.assertTrue(row["is_gap_scope_missing"])
        self.assertTrue(row["is_gap_partial"])
        self.assertIn("endpoint_user_device", row["scope_summary"]["full_scopes"])
        self.assertIn("server", row["scope_summary"]["missing_scopes"])

    def test_full_scope_assignment_removes_scope_gap(self):
        tool = self._create_tool("Full DLP", "DLP")
        capability = self._find_capability("CAP-007")
        self._assign_capability(tool["id"], capability["id"], "block", "full")
        self._set_scopes(
            tool["id"],
            capability["id"],
            [
                ("endpoint_user_device", "full", "Endpoints"),
                ("server", "full", "Servers"),
                ("cloud_workload", "full", "Cloud workloads"),
            ],
        )

        row = next(item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1041")
        self.assertEqual(row["effective_control_effect"], "block")
        self.assertFalse(row["is_gap_scope_missing"])
        self.assertFalse(row["is_gap_scope_partial"])

    def test_capability_without_scope_is_not_valid_global_coverage(self):
        tool = self._create_tool("Unknown Scope DLP", "DLP")
        capability = self._find_capability("CAP-007")
        self._assign_capability(tool["id"], capability["id"], "block", "full")

        row = next(item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1041")
        self.assertEqual(row["effective_control_effect"], "none")
        self.assertTrue(row["is_gap_scope_missing"])
        self.assertEqual(row["confidence_level"], "low")

    def test_missing_critical_public_facing_scope_keeps_t1190_as_gap(self):
        tool = self._create_tool("Edge Firewall", "Other")
        capability = self._find_capability("CAP-031")
        self._assign_capability(tool["id"], capability["id"], "prevent", "full")
        self._set_scopes(tool["id"], capability["id"], [("server", "full", "Internal servers only")])
        self._verify_configuration(tool["id"], capability["id"], ["yes", "yes", "yes", "yes"])

        row = next(item for item in self.client.get("/coverage").json() if item["technique_code"] == "T1190")
        self.assertEqual(row["effective_control_effect"], "none")
        self.assertTrue(row["is_gap_scope_missing"])

    def test_tool_tags_can_be_updated(self):
        tool = self._create_tool("Specops", "Identity")
        response = self.client.put(
            f"/tools/{tool['id']}/tags",
            json={"tags": ["Active Directory", "Password Security", "Credential Hygiene"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["tags"],
            ["Active Directory", "Password Security", "Credential Hygiene"],
        )

    def test_capability_detail_includes_tools_answers_and_related_techniques(self):
        tool = self._create_tool("Identity Control", "PAM")
        capability = self._find_capability("CAP-009")
        self._assign_capability(tool["id"], capability["id"], "detect", "full")

        template = self.client.get(f"/capabilities/{capability['id']}/assessment-template").json()
        self.client.post(
            f"/tools/{tool['id']}/capabilities/{capability['id']}/assessment-answers",
            json={
                "answers": [
                    {"question_id": template["questions"][0]["id"], "answer": "yes"},
                    {"question_id": template["questions"][1]["id"], "answer": "partial"},
                ]
            },
        )

        detail = self.client.get(f"/capabilities/{capability['id']}")
        self.assertEqual(detail.status_code, 200)
        payload = detail.json()
        self.assertEqual(payload["capability"]["code"], "CAP-009")
        self.assertGreater(len(payload["related_techniques"]), 0)
        self.assertEqual(payload["implementing_tools"][0]["tool_name"], "Identity Control")
        self.assertEqual(len(payload["implementing_tools"][0]["assessment_answers"]), 2)

    def test_docs_endpoints_return_dynamic_tool_types_capabilities_and_mappings(self):
        analytics_tool = self._create_tool("QRadar", "Security Analytics", "analytics")
        response_tool = self._create_tool("XSOAR", "SOAR", "response")
        control_tool = self._create_tool("Mail Gateway", "Email", "control")

        identity_capability = self._find_capability("CAP-009")
        phishing_capability = self._find_capability("CAP-004")

        self._assign_capability(analytics_tool["id"], identity_capability["id"], "detect", "full")
        self._assign_capability(response_tool["id"], identity_capability["id"], "detect", "partial")
        self._assign_capability(control_tool["id"], phishing_capability["id"], "prevent", "full")

        tool_type_rows = self.client.get("/docs/tool-types")
        self.assertEqual(tool_type_rows.status_code, 200)
        analytics_row = next(item for item in tool_type_rows.json() if item["tool_type"] == "analytics")
        self.assertIn("QRadar", analytics_row["example_usage"])

        capability_rows = self.client.get("/docs/capabilities")
        self.assertEqual(capability_rows.status_code, 200)
        identity_row = next(item for item in capability_rows.json() if item["capability"]["code"] == "CAP-009")
        self.assertIn("analytics", identity_row["tool_types"])
        self.assertGreater(len(identity_row["related_techniques"]), 0)

        mapping_rows = self.client.get("/docs/mappings")
        self.assertEqual(mapping_rows.status_code, 200)
        analytics_mapping = next(item for item in mapping_rows.json()["tool_type_mappings"] if item["tool_type"] == "analytics")
        self.assertTrue(any(capability["code"] == "CAP-009" for capability in analytics_mapping["capabilities"]))
        capability_mapping = next(
            item for item in mapping_rows.json()["capability_mappings"] if item["capability"]["code"] == "CAP-009"
        )
        self.assertIn("analytics", capability_mapping["tool_types"])

    def test_generic_capability_roles_are_exposed(self):
        capabilities = self.client.get("/capabilities").json()
        correlation = next(item for item in capabilities if item["code"] == "CAP-134")
        self.assertEqual(correlation["name"], "Security Event Correlation")
        self.assertEqual(
            [role["code"] for role in correlation["coverage_roles"]],
            ["alert", "detect"],
        )

    def test_known_tool_normalization_enriches_existing_tools_without_duplicates(self):
        tool = self._create_tool("QRadar", "Security Analytics", "analytics")

        with self.session_local() as db:
            seed_reference_data(db)
            seed_reference_data(db)

        payload = self.client.get(f"/tools/{tool['id']}").json()
        capability_ids = sorted(item["capability_id"] for item in payload["capabilities"])

        self.assertEqual(payload["vendor"]["name"], "IBM")
        self.assertIn("SIEM", payload["tool_type_labels"])
        self.assertIn("analytics", payload["tool_types"])
        self.assertEqual(capability_ids.count(self._find_capability("CAP-134")["id"]), 1)
        self.assertEqual(capability_ids.count(self._find_capability("CAP-135")["id"]), 1)

    def test_migrate_legacy_database_preserves_existing_records_and_creates_backup(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            temp_path = Path(temp_dir.name)
            database_path = temp_path / "legacy.db"
            with sqlite3.connect(database_path) as connection:
                connection.executescript(
                    """
                    CREATE TABLE tools (
                      id INTEGER PRIMARY KEY,
                      name TEXT NOT NULL,
                      category TEXT NOT NULL,
                      tool_type TEXT NOT NULL
                    );
                    CREATE TABLE capabilities (
                      id INTEGER PRIMARY KEY,
                      code TEXT NOT NULL,
                      name TEXT NOT NULL,
                      domain TEXT NOT NULL
                    );
                    CREATE TABLE techniques (
                      id INTEGER PRIMARY KEY,
                      code TEXT NOT NULL,
                      name TEXT NOT NULL
                    );
                    CREATE TABLE tool_capabilities (
                      id INTEGER PRIMARY KEY,
                      tool_id INTEGER NOT NULL,
                      capability_id INTEGER NOT NULL,
                      implementation_level TEXT NOT NULL,
                      control_effect TEXT NOT NULL,
                      confidence_source TEXT NOT NULL,
                      confidence_level TEXT NOT NULL
                    );
                    CREATE TABLE tool_capability_evidence (
                      id INTEGER PRIMARY KEY,
                      tool_id INTEGER NOT NULL,
                      capability_id INTEGER NOT NULL,
                      title TEXT NOT NULL,
                      evidence_type TEXT NOT NULL,
                      note TEXT NOT NULL,
                      file_name TEXT,
                      recorded_at TEXT NOT NULL
                    );
                    CREATE TABLE data_sources (
                      id INTEGER PRIMARY KEY,
                      code TEXT NOT NULL,
                      name TEXT NOT NULL,
                      category TEXT NOT NULL,
                      description TEXT NOT NULL
                    );
                    CREATE TABLE tool_data_sources (
                      id INTEGER PRIMARY KEY,
                      tool_id INTEGER NOT NULL,
                      data_source_id INTEGER NOT NULL,
                      ingestion_status TEXT NOT NULL,
                      notes TEXT NOT NULL
                    );
                    CREATE TABLE response_actions (
                      id INTEGER PRIMARY KEY,
                      code TEXT NOT NULL,
                      name TEXT NOT NULL,
                      description TEXT NOT NULL
                    );
                    CREATE TABLE tool_response_actions (
                      id INTEGER PRIMARY KEY,
                      tool_id INTEGER NOT NULL,
                      response_action_id INTEGER NOT NULL,
                      implementation_level TEXT NOT NULL,
                      notes TEXT NOT NULL
                    );
                    CREATE TABLE coverage_scopes (
                      id INTEGER PRIMARY KEY,
                      code TEXT NOT NULL,
                      name TEXT NOT NULL,
                      description TEXT NOT NULL
                    );
                    CREATE TABLE tool_capability_scopes (
                      id INTEGER PRIMARY KEY,
                      tool_capability_id INTEGER NOT NULL,
                      coverage_scope_id INTEGER NOT NULL,
                      status TEXT NOT NULL,
                      notes TEXT NOT NULL
                    );
                    CREATE TABLE bas_validations (
                      id INTEGER PRIMARY KEY,
                      technique_id INTEGER NOT NULL,
                      bas_tool_id INTEGER,
                      bas_result TEXT NOT NULL,
                      last_validation_date TEXT,
                      notes TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    "INSERT INTO tools (id, name, category, tool_type) VALUES (1, 'Legacy QRadar', 'Security Analytics', 'analytics')"
                )
                connection.execute(
                    "INSERT INTO capabilities (id, code, name, domain) VALUES (9, 'CAP-009', 'Identity Misuse Detection', 'identity')"
                )
                connection.execute(
                    "INSERT INTO techniques (id, code, name) VALUES (1, 'T1078', 'Valid Accounts')"
                )
                connection.execute(
                    """
                    INSERT INTO tool_capabilities
                    (id, tool_id, capability_id, implementation_level, control_effect, confidence_source, confidence_level)
                    VALUES (10, 1, 9, 'full', 'detect', 'evidenced', 'high')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO tool_capability_evidence
                    (id, tool_id, capability_id, title, evidence_type, note, file_name, recorded_at)
                    VALUES (1, 1, 9, 'Legacy export', 'config', 'Preserve this', 'legacy.json', '2026-04-01')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO data_sources (id, code, name, category, description)
                    VALUES (1, 'DS-001', 'Active Directory Logs', 'identity', 'Directory logs')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO tool_data_sources (id, tool_id, data_source_id, ingestion_status, notes)
                    VALUES (1, 1, 1, 'full', 'Already ingested')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO response_actions (id, code, name, description)
                    VALUES (1, 'RA-002', 'Disable Account', 'Disable account')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO tool_response_actions (id, tool_id, response_action_id, implementation_level, notes)
                    VALUES (1, 1, 1, 'partial', 'Available playbook')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO coverage_scopes (id, code, name, description)
                    VALUES (4, 'identity', 'Identity', 'Identity systems')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO tool_capability_scopes (id, tool_capability_id, coverage_scope_id, status, notes)
                    VALUES (1, 10, 4, 'full', 'Identity path covered')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO bas_validations (id, technique_id, bas_tool_id, bas_result, last_validation_date, notes)
                    VALUES (1, 1, 1, 'detected', '2026-04-10', 'Legacy BAS record')
                    """
                )
                connection.commit()

            backup_path = migrate_legacy_database(database_path)

            self.assertIsNotNone(backup_path)
            self.assertTrue(Path(backup_path).exists())

            with sqlite3.connect(database_path) as connection:
                tool_row = connection.execute(
                    "SELECT name, category, tool_types FROM tools WHERE id = 1"
                ).fetchone()
                capability_row = connection.execute(
                    """
                    SELECT tc.control_effect_default, tc.implementation_level, tc.confidence_source, tc.confidence_level
                    FROM tool_capabilities tc
                    JOIN capabilities c ON c.id = tc.capability_id
                    WHERE tc.tool_id = 1 AND c.code = 'CAP-009'
                    """
                ).fetchone()
                evidence_row = connection.execute(
                    "SELECT title, file_name FROM tool_capability_evidence WHERE tool_id = 1"
                ).fetchone()
                data_source_row = connection.execute(
                    "SELECT ingestion_status FROM tool_data_sources WHERE tool_id = 1"
                ).fetchone()
                response_action_row = connection.execute(
                    "SELECT implementation_level FROM tool_response_actions WHERE tool_id = 1"
                ).fetchone()
                scope_row = connection.execute(
                    """
                    SELECT tcs.status
                    FROM tool_capability_scopes tcs
                    JOIN tool_capabilities tc ON tc.id = tcs.tool_capability_id
                    JOIN capabilities c ON c.id = tc.capability_id
                    WHERE tc.tool_id = 1 AND c.code = 'CAP-009'
                    """
                ).fetchone()
                bas_row = connection.execute(
                    "SELECT bas_result, last_validation_date FROM bas_validations WHERE bas_tool_id = 1"
                ).fetchone()

            self.assertEqual(tool_row[0], "Legacy QRadar")
            self.assertEqual(tool_row[1], "Security Analytics & Detection (SIEM / UEBA)")
            self.assertEqual(json.loads(tool_row[2]), ["analytics"])
            self.assertEqual(capability_row, ("detect", "full", "evidenced", "high"))
            self.assertEqual(evidence_row, ("Legacy export", "legacy.json"))
            self.assertEqual(data_source_row[0], "full")
            self.assertEqual(response_action_row[0], "partial")
            self.assertEqual(scope_row[0], "full")
            self.assertEqual(bas_row, ("detected", "2026-04-10"))
        finally:
            try:
                temp_dir.cleanup()
            except PermissionError:
                pass


if __name__ == "__main__":
    unittest.main()
