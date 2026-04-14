from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models import ToolCapability, ToolCapabilityConfigurationProfile


CONFIGURATION_ANSWER_SCORES = {
    "yes": 2,
    "partial": 1,
    "no": 0,
    "unknown": 0,
}

CONFIGURATION_STATUS_RANK = {
    "unknown": 0,
    "not_enabled": 1,
    "partially_enabled": 2,
    "enabled": 3,
}


@dataclass
class ConfigurationSummary:
    configuration_status: str
    answered_questions: int
    total_questions: int
    score: int
    max_score: int


def calculate_configuration_status(
    profile: ToolCapabilityConfigurationProfile | None,
    total_questions: int,
) -> ConfigurationSummary:
    answers = list(profile.tool_capability.configuration_answers) if profile else []
    answered_questions = len(answers)
    score = sum(CONFIGURATION_ANSWER_SCORES[answer.answer] for answer in answers)
    max_score = total_questions * 2

    if profile is None:
        status = "unknown"
    elif answered_questions == 0:
        status = profile.configuration_status or "unknown"
    else:
        status = _score_to_status(score, max_score)

    return ConfigurationSummary(
        configuration_status=status,
        answered_questions=answered_questions,
        total_questions=total_questions,
        score=score,
        max_score=max_score,
    )


def sync_tool_capability_configuration(tool_capability: ToolCapability) -> ConfigurationSummary:
    capability = tool_capability.capability
    profile = tool_capability.configuration_profile
    total_questions = len(capability.configuration_questions)

    if not capability.requires_configuration:
        if profile is not None:
            profile.configuration_status = "enabled"
            profile.profile_type = capability.configuration_profile_type
            profile.last_updated_at = _now_iso()
        return ConfigurationSummary(
            configuration_status="enabled",
            answered_questions=0,
            total_questions=0,
            score=0,
            max_score=0,
        )

    summary = calculate_configuration_status(profile, total_questions)
    if profile is not None:
        profile.configuration_status = summary.configuration_status
        profile.profile_type = capability.configuration_profile_type
        profile.last_updated_at = _now_iso()
    return summary


def ensure_configuration_profile(tool_capability: ToolCapability) -> ToolCapabilityConfigurationProfile:
    profile = tool_capability.configuration_profile
    if profile is None:
        profile = ToolCapabilityConfigurationProfile(
            tool_id=tool_capability.tool_id,
            capability_id=tool_capability.capability_id,
            profile_type=tool_capability.capability.configuration_profile_type,
            configuration_status="unknown",
            notes="",
            last_updated_at=_now_iso(),
        )
        tool_capability.configuration_profile = profile
    return profile


def _score_to_status(score: int, max_score: int) -> str:
    if max_score <= 0:
        return "unknown"

    ratio = score / max_score
    if ratio >= 0.75:
        return "enabled"
    if ratio >= 0.35:
        return "partially_enabled"
    return "not_enabled"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
