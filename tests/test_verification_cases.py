"""期待診断の欠落や別原因の失敗を共通判定器で拒否する。"""

import subprocess
import sys
from pathlib import Path

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


@pytest.mark.parametrize(
    "category,code,output,rejected",
    [
        ("verified", 1, "Java not found", True),
        ("proof_failure", 1, "Verification failed unrelated reason", True),
        ("verified", 0, "Verification successful", False),
        ("proof_failure", 1, "Verification failed target diagnostic", False),
    ],
)
def test_optimized_process_keeps_verification_gate(
    category: str, code: int, output: str, rejected: bool
) -> None:
    """Python -Oでも誤った診断を拒否し、正しい診断を受理する。"""
    probe = """
import sys
from pathlib import Path
from unittest.mock import patch
from scripts.verification_cases import (
    ExpectedVerification, Specification, VerificationCase, verify_case,
)
category, code, output = sys.argv[1:]
diagnostics = ('target diagnostic',) if category == 'proof_failure' else ()
case = VerificationCase('optimized', Specification('static', 'runtime'),
                        ExpectedVerification(category, diagnostics))
with patch('scripts.check.run', return_value=(int(code), output)):
    try:
        verify_case(case, Path('unused.py'))
    except AssertionError:
        print('rejected')
        raise SystemExit(3)
print('accepted')
"""
    root = Path(__file__).resolve().parents[1]
    process = subprocess.run(
        [sys.executable, "-O", "-c", probe, category, str(code), output],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert process.returncode == (3 if rejected else 0), process.stdout + process.stderr
    assert process.stdout.strip() == ("rejected" if rejected else "accepted")


@pytest.mark.parametrize(
    "code,output,expected",
    (
        (1, "Translation failed\nNot supported: target (probe.py@2.3)", True),
        (0, "Translation failed\nNot supported: target (probe.py@2.3)", False),
        (2, "Translation failed\nNot supported: target (probe.py@2.3)", False),
        (1, "Translation failed\nNot supported: other (probe.py@2.3)", False),
        (1, "Translation failed\nNot supported: target (probe.py@2.4)", False),
        (1, "Java not found", False),
        (1, "Verification failed\nNot supported: target (probe.py@2.3)", False),
        (1, "Translation failed Not supported: target (probe.py@2.3) Verification failed", False),
        (1, "Translation failed Not supported: target (probe.py@2.3) Verification successful", False),
    ),
)
def test_translation_failure_is_separate(code: int, output: str, expected: bool) -> None:
    """変換失敗を狙った全文位置で照合し証明失敗や起動障害を排除する。"""
    result = ExpectedVerification("translation_failure", ("Not supported: target (probe.py@2.3)",))
    assert result.matches(code, output) is expected


def test_translation_failure_needs_diagnostics() -> None:
    """変換失敗にも原因と位置の診断を必須にする。"""
    with pytest.raises(ValueError):
        ExpectedVerification("translation_failure")
