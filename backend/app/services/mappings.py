from app.models import Capability, CapabilityTechniqueMap


MAPPING_COVERAGE_PRIORITY = {
    "partial": 0,
    "full": 1,
}


def get_structural_technique_maps(capability: Capability) -> list[CapabilityTechniqueMap]:
    representatives: dict[int, CapabilityTechniqueMap] = {}

    for mapping in capability.technique_maps:
        current = representatives.get(mapping.technique_id)
        if current is None:
            representatives[mapping.technique_id] = mapping
            continue

        if MAPPING_COVERAGE_PRIORITY[mapping.coverage] > MAPPING_COVERAGE_PRIORITY[current.coverage]:
            representatives[mapping.technique_id] = mapping

    return sorted(representatives.values(), key=lambda item: item.technique.code)
