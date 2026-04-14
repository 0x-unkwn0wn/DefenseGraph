from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Tool, ToolCapability, ToolCapabilityTemplate
from app.schemas import ToolCapabilityTemplateApplyItem
from app.seed import CATEGORY_DEFAULT_TAGS, TOOL_TAGS


TEMPLATE_PRIORITY_RANK = {"core": 2, "secondary": 1, "niche": 0}
SUGGESTION_GROUP_RANK = {"core": 2, "recommended": 1, "optional": 0}


@dataclass
class RankedTemplate:
    template: ToolCapabilityTemplate
    matched_tags: list[str]
    suggestion_group: str


def list_available_tags() -> list[dict[str, object]]:
    return TOOL_TAGS


def get_default_tags_for_category(category: str) -> list[str]:
    return CATEGORY_DEFAULT_TAGS.get(category, [])


def get_ranked_templates(db: Session, category: str, tags: list[str]) -> list[RankedTemplate]:
    statement = (
        select(ToolCapabilityTemplate)
        .options(joinedload(ToolCapabilityTemplate.capability))
        .where(ToolCapabilityTemplate.category == category)
        .order_by(ToolCapabilityTemplate.id)
    )
    templates = db.execute(statement).unique().scalars().all()
    normalized_tags = {tag.strip() for tag in tags if tag.strip()}

    ranked_by_capability: dict[int, RankedTemplate] = {}
    for template in templates:
        matched_tags = sorted(normalized_tags.intersection(template.optional_tags))
        suggestion_group = _determine_suggestion_group(template.priority, matched_tags)
        ranked = RankedTemplate(
            template=template,
            matched_tags=matched_tags,
            suggestion_group=suggestion_group,
        )

        current = ranked_by_capability.get(template.capability_id)
        if current is None or _should_replace(current, ranked):
            ranked_by_capability[template.capability_id] = ranked

    ranked_templates = list(ranked_by_capability.values())
    ranked_templates.sort(
        key=lambda item: (
            -SUGGESTION_GROUP_RANK[item.suggestion_group],
            -TEMPLATE_PRIORITY_RANK[item.template.priority],
            item.template.capability.name,
        )
    )
    return ranked_templates


def apply_templates_to_tool(
    db: Session,
    tool: Tool,
    selected_templates: list[ToolCapabilityTemplateApplyItem],
) -> Tool:
    if not selected_templates:
        return tool

    template_ids = [item.template_id for item in selected_templates]
    templates = {
        template.id: template
        for template in db.execute(
            select(ToolCapabilityTemplate)
            .options(joinedload(ToolCapabilityTemplate.capability))
            .where(ToolCapabilityTemplate.id.in_(template_ids))
        ).unique().scalars().all()
    }

    for item in selected_templates:
        template = templates.get(item.template_id)
        if template is None or template.category != tool.category:
            continue

        assignment = db.scalar(
            select(ToolCapability).where(
                ToolCapability.tool_id == tool.id,
                ToolCapability.capability_id == template.capability_id,
            )
        )
        if assignment is None:
            assignment = ToolCapability(
                tool_id=tool.id,
                capability_id=template.capability_id,
                control_effect=item.control_effect or template.default_effect,
                implementation_level=item.implementation_level or template.default_implementation_level,
            )
            db.add(assignment)
        else:
            assignment.control_effect = item.control_effect or template.default_effect
            assignment.implementation_level = item.implementation_level or template.default_implementation_level

    db.commit()
    db.refresh(tool)
    return tool


def _determine_suggestion_group(priority: str, matched_tags: list[str]) -> str:
    if priority == "core":
        return "core"
    if matched_tags:
        return "recommended"
    return "optional"


def _should_replace(current: RankedTemplate, candidate: RankedTemplate) -> bool:
    if SUGGESTION_GROUP_RANK[candidate.suggestion_group] != SUGGESTION_GROUP_RANK[current.suggestion_group]:
        return SUGGESTION_GROUP_RANK[candidate.suggestion_group] > SUGGESTION_GROUP_RANK[current.suggestion_group]

    if TEMPLATE_PRIORITY_RANK[candidate.template.priority] != TEMPLATE_PRIORITY_RANK[current.template.priority]:
        return TEMPLATE_PRIORITY_RANK[candidate.template.priority] > TEMPLATE_PRIORITY_RANK[current.template.priority]

    return len(candidate.matched_tags) > len(current.matched_tags)
