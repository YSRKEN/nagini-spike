"""期待診断の欠落や別原因の失敗を共通判定器で拒否する。"""

import pytest

from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
)

SPEC = Specification("結果が非負である", "absと照合する")
GOOD = VerificationCase("正例", SPEC, ExpectedVerification("verified"))
BAD = VerificationCase(
    "誤例",
    SPEC,
    ExpectedVerification("proof_failure", ("Postcondition", "Assertion result >= 0", "(5:4)")),
    Mutation("return -x", "return x"),
)


@pytest.mark.parametrize(
    "code,output,expected",
    [
        (0, "Verification successful", True),
        (1, "Verification successful", False),
        (0, "", False),
        (0, "Verification successful\nVerification failed", False),
    ],
)
def test_success_requires_consistent_evidence(code: int, output: str, expected: bool) -> None:
    """成功コードと成功診断が揃い、失敗診断が混ざらない場合だけ受理する。"""
    assert GOOD.expected.matches(code, output) is expected


@pytest.mark.parametrize(
    "code,output,expected",
    [
        (1, "Verification failed Postcondition Assertion result >= 0 (5:4)", True),
        (1, "Verification failed Assertion result >= 0 (5:4)", False),
        (1, "Verification failed Postcondition Assertion result >= 0 (6:4)", False),
        (1, "Java not found", False),
        (1, "Verification failed Syntax error", False),
        (0, "Verification failed Postcondition Assertion result >= 0 (5:4)", False),
        (2, "Verification failed Postcondition Assertion result >= 0 (5:4)", False),
        (
            1,
            "Verification failed Postcondition Assertion result >= 0 (5:4) Verification successful",
            False,
        ),
    ],
)
def test_failure_requires_every_target(code: int, output: str, expected: bool) -> None:
    """必須の診断・位置が全て揃った証明失敗だけ受理する。"""
    assert BAD.expected.matches(code, output) is expected


def test_proof_failure_needs_diagnostics() -> None:
    """一般的な失敗だけを期待値にできない。"""
    with pytest.raises(ValueError):
        ExpectedVerification("proof_failure")


def test_success_cannot_require_failure_diagnostics() -> None:
    """成功の期待値に矛盾する診断を持たせない。"""
    with pytest.raises(ValueError):
        ExpectedVerification("verified", ("Postcondition",))


@pytest.mark.parametrize("source", ["pass", "return -x\nreturn -x"])
def test_mutation_requires_one_source(source: str) -> None:
    """変更箇所が失われたり増えたりしたら早く拒否する。"""
    with pytest.raises(ValueError):
        Mutation("return -x", "return x").apply(source)


def test_mutation_keeps_other_source() -> None:
    """狙った一箇所だけを変更する。"""
    assert Mutation("return -x", "return x").apply("if x < 0: return -x\nreturn x") == (
        "if x < 0: return x\nreturn x"
    )
