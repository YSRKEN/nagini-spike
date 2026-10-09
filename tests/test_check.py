"""環境の故障を、証明の成功や誤実装の拒否と取り違えない。"""

import pytest

from scripts.check import accepted, rejected, timeout_for


@pytest.mark.parametrize(
    ("returncode", "output", "expected"),
    [(0, "Verification successful", True), (0, "", False), (1, "Verification successful", False)],
)
def test_accepted_requires_success(returncode: int, output: str, expected: bool) -> None:
    """終了コードと成功の診断が両方揃った場合だけ合格する。"""
    assert accepted(returncode, output) is expected


@pytest.mark.parametrize(
    ("returncode", "output", "expected"),
    [
        (1, "Verification failed\nAssertion result >= 0 might not hold.", True),
        (1, "Java not found", False),
        (1, "Verification failed\nSyntax error", False),
        (0, "Verification failed\nAssertion result >= 0 might not hold.", False),
    ],
)
def test_rejected_requires_target_failure(returncode: int, output: str, expected: bool) -> None:
    """狙った条件の検証失敗と、起動・構文エラーを区別する。"""
    assert rejected(returncode, output) is expected


@pytest.mark.parametrize(
    "arguments,expected",
    [
        (["-m", "pytest", "-q", "tests"], 600),
        (["-m", "nagini_translation.main", "examples/list_head.py"], 90),
        (["-m", "ruff", "check", "examples"], 90),
    ],
)
def test_timeout_distinguishes_suite(arguments: list[str], expected: int) -> None:
    """個々の検証の上限を維持し、検証をまとめるテストだけ時間を確保する。"""
    assert timeout_for(arguments) == expected
