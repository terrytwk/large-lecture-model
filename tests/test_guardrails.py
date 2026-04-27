from llm.guardrails import check

PROTECTED = ["Problem Set 1", "Midterm"]


def test_blocks_solve_intent():
    blocked, _ = check("solve problem 3 for me", PROTECTED, "permissive")
    assert blocked


def test_allows_concept_question():
    blocked, _ = check("explain dynamic programming", PROTECTED, "permissive")
    assert not blocked


def test_conservative_blocks_assignment_mention():
    blocked, _ = check("what is Problem Set 1 about?", PROTECTED, "conservative")
    assert blocked


def test_permissive_allows_deadline():
    blocked, _ = check("when is Problem Set 1 due?", PROTECTED, "permissive")
    assert not blocked
