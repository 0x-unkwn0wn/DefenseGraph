TEST_STATUS_RANK = {
    "not_tested": 0,
    "passed": 1,
    "partial": 2,
    "detected_not_blocked": 3,
    "failed": 4,
}

LEGACY_TO_TEST_STATUS = {
    "blocked": "passed",
    "detected": "detected_not_blocked",
    "not_detected": "failed",
    "not_tested": "not_tested",
}

TEST_STATUS_TO_LEGACY = {
    "passed": "blocked",
    "partial": "detected",
    "detected_not_blocked": "detected",
    "failed": "not_detected",
    "not_tested": "not_tested",
}


def normalize_test_status(value: str | None) -> str:
    if not value:
        return "not_tested"
    if value in TEST_STATUS_RANK:
        return value
    return LEGACY_TO_TEST_STATUS.get(value, "not_tested")


def to_legacy_bas_result(test_status: str) -> str:
    return TEST_STATUS_TO_LEGACY.get(normalize_test_status(test_status), "not_tested")


def build_test_status_summary(values: list[str]) -> dict[str, int]:
    summary = {status: 0 for status in TEST_STATUS_RANK}
    for value in values:
        summary[normalize_test_status(value)] += 1
    return summary


def strongest_test_status(values: list[str]) -> str:
    if not values:
        return "not_tested"
    return max((normalize_test_status(value) for value in values), key=lambda value: TEST_STATUS_RANK[value])
