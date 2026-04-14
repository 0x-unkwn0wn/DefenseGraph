from __future__ import annotations

from dataclasses import dataclass

from app.models import ToolCapability
from app.services.configuration import calculate_configuration_status


ANSWER_SCORES = {
    "yes": 2,
    "partial": 1,
    "no": 0,
    "unknown": 0,
}

CONFIDENCE_RANK = {
    "low": 0,
    "medium": 1,
    "high": 2,
}

SOURCE_RANK = {
    "declared": 0,
    "assessed": 1,
    "evidenced": 2,
    "tested": 3,
}


@dataclass
class ConfidenceSummary:
    confidence_source: str
    confidence_level: str
    answered_questions: int
    total_questions: int
    score: int
    max_score: int
    evidence_count: int


def calculate_confidence(tool_capability: ToolCapability, total_questions: int) -> ConfidenceSummary:
    answers = list(tool_capability.assessment_answers)
    evidence_items = list(tool_capability.evidence_items)

    answered_questions = len(answers)
    score = sum(ANSWER_SCORES[answer.answer] for answer in answers)
    max_score = total_questions * 2

    if answered_questions == 0:
        base_level = "low"
    else:
        base_level = _score_to_level(score, max_score)

    if answered_questions == 0:
        confidence_source = "declared"
        confidence_level = "low"
    else:
        confidence_source = "assessed"
        confidence_level = base_level

    if evidence_items:
        confidence_source = "evidenced"
        confidence_level = max(confidence_level, "medium", key=lambda level: CONFIDENCE_RANK[level])

    if tool_capability.confidence_source == "tested":
        confidence_source = "tested"
        confidence_level = "high"

    configuration_status = _get_configuration_status(tool_capability)
    if tool_capability.capability.requires_configuration:
        if configuration_status in {"unknown", "not_enabled"}:
            confidence_level = "low"
            if not evidence_items and tool_capability.confidence_source != "tested":
                confidence_source = "declared"
        elif (
            configuration_status == "partially_enabled"
            and confidence_source not in {"evidenced", "tested"}
            and CONFIDENCE_RANK[confidence_level] > CONFIDENCE_RANK["medium"]
        ):
            confidence_level = "medium"

    return ConfidenceSummary(
        confidence_source=confidence_source,
        confidence_level=confidence_level,
        answered_questions=answered_questions,
        total_questions=total_questions,
        score=score,
        max_score=max_score,
        evidence_count=len(evidence_items),
    )


def sync_tool_capability_confidence(tool_capability: ToolCapability) -> ConfidenceSummary:
    total_questions = (
        len(tool_capability.capability.assessment_template.questions)
        if tool_capability.capability.assessment_template
        else 0
    )
    summary = calculate_confidence(tool_capability, total_questions)
    tool_capability.confidence_source = summary.confidence_source
    tool_capability.confidence_level = summary.confidence_level
    return summary


def _score_to_level(score: int, max_score: int) -> str:
    if max_score <= 0:
        return "low"

    ratio = score / max_score
    if ratio >= 0.75:
        return "high"
    if ratio >= 0.35:
        return "medium"
    return "low"


def _get_configuration_status(tool_capability: ToolCapability) -> str:
    if not tool_capability.capability.requires_configuration:
        return "enabled"

    summary = calculate_configuration_status(
        tool_capability.configuration_profile,
        len(tool_capability.capability.configuration_questions),
    )
    return summary.configuration_status
