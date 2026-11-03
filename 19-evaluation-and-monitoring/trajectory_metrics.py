from collections import Counter


def exact_match(actual: list[str], expected: list[str]) -> bool:
    return actual == expected


def in_order_match(actual: list[str], expected: list[str]) -> bool:
    remaining = iter(actual)
    return all(step in remaining for step in expected)


def any_order_match(actual: list[str], expected: list[str]) -> bool:
    return not (Counter(expected) - Counter(actual))


def precision(actual: list[str], expected: list[str]) -> float:
    return sum((Counter(actual) & Counter(expected)).values()) / len(actual) if actual else 0.0


def recall(actual: list[str], expected: list[str]) -> float:
    return sum((Counter(actual) & Counter(expected)).values()) / len(expected) if expected else 1.0


def score(actual: list[str], expected: list[str]) -> dict:
    return {
        "exact": exact_match(actual, expected),
        "in_order": in_order_match(actual, expected),
        "any_order": any_order_match(actual, expected),
        "precision": round(precision(actual, expected), 2),
        "recall": round(recall(actual, expected), 2),
    }


if __name__ == "__main__":
    expected = ["search_db", "summarize"]
    assert score(["search_db", "summarize"], expected)["exact"]
    assert score(["search_db", "log", "summarize"], expected) == {
        "exact": False, "in_order": True, "any_order": True, "precision": 0.67, "recall": 1.0,
    }
    assert score(["summarize", "search_db"], expected)["in_order"] is False
    assert score(["summarize"], expected)["recall"] == 0.5
    print("trajectory metrics ok")
