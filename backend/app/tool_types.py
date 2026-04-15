LEGACY_TOOL_TYPE_ALIASES = {
    "assurance": "validated",
}


def normalize_tool_types(tool_types: list[str]) -> list[str]:
    normalized: list[str] = []

    for tool_type in tool_types:
        canonical = LEGACY_TOOL_TYPE_ALIASES.get(tool_type, tool_type)
        if canonical not in normalized:
            normalized.append(canonical)

    return normalized


def is_validated_tool(tool_types: list[str]) -> bool:
    return "validated" in normalize_tool_types(tool_types)
