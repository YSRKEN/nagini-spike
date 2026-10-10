"""有限例を通る偽階乗を独立した一般契約と比較する。"""

import math
from pathlib import Path
from typing import Callable, cast

import pytest

import scripts.check as check
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "非負整数全体でResult()==fac(n)。独立Pure定義はfac(0)=1、fac(n)=n*fac(n-1)",
    "検証に使った同一ソースのEnsures一行だけを除き、有限例とmath.factorialを照合する",
)
SOURCE = Path(__file__).resolve().parents[1] / "examples" / "factorial_general.py"
CORRECT_BODY = "    if n == 0:\n        return 1\n    return n * factorial(n - 1)\n"
FAKE_BODY = (
    "    return ((((((24 * n - 240) * n + 849) * n - 1246) * n + 663) * n - 50) * n + 24) // 24\n"
)


def runtime_functions(source: str) -> tuple[Callable[[int], int], Callable[[int], int]]:
    """照合した宣言一行だけを除き、計算本体とモデルを実行する。"""
    declaration = "    Ensures(Result() == fac(n))\n"
    assert source.count(declaration) == 1
    runtime = source.replace(declaration, "\n")
    assert "Ensures(" not in runtime
    namespace: dict[str, object] = {}
    exec(compile(runtime, "runtime_factorial.py", "exec"), namespace)
    return (
        cast(Callable[[int], int], namespace["factorial"]),
        cast(Callable[[int], int], namespace["fac"]),
    )


def test_correct_general_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """正実装を検証した後、同じ計算本体とモデルを通常実行で照合する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("factorial_general", SPECIFICATION, ExpectedVerification("verified")),
        SOURCE,
    )
    calculate, model = runtime_functions(SOURCE.read_text(encoding="utf-8"))
    for n in (0, 1, 2, 3, 4, 5, 10, 50, 100):
        assert calculate(n) == model(n) == math.factorial(n)
    with pytest.raises(RecursionError):
        calculate(10_000)


def test_fake_finite_examples_and_general_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """有限例の全合格と一般事後条件での拒否を同じ変更例で確認する。"""
    source = SOURCE.read_text(encoding="utf-8")
    mutation = Mutation(CORRECT_BODY, FAKE_BODY)
    changed = mutation.apply(source)
    assert "Requires(n >= 0)" in changed
    assert "n <= 4" not in changed
    path = tmp_path / "factorial_fake.py"
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "factorial_fake",
            SPECIFICATION,
            ExpectedVerification(
                "proof_failure",
                (
                    "Postcondition of factorial might not hold.",
                    "Assertion Result() == fac(n) might not hold.",
                ),
            ),
            mutation,
        ),
        path,
    )
    calculate, model = runtime_functions(changed)
    observations = [(n, calculate(n), math.factorial(n)) for n in range(6)]
    assert observations == [(0, 1, 1), (1, 1, 1), (2, 2, 2), (3, 6, 6), (4, 24, 24), (5, 676, 120)]
    polynomial_at_five = (
        1 + 5 * 4 // 2 + 5 * 4 * 3 // 3 + 3 * 5 * 4 * 3 * 2 // 8 + 5 * 5 * 4 * 3 * 2
    )
    assert polynomial_at_five == calculate(5)
    assert model(5) == 120
    for n in range(101):
        original = (
            1
            + n * (n - 1) // 2
            + n * (n - 1) * (n - 2) // 3
            + 3 * n * (n - 1) * (n - 2) * (n - 3) // 8
            + n * n * (n - 1) * (n - 2) * (n - 3) * (n - 4)
        )
        assert calculate(n) == original


def test_horner_coefficients_are_exact() -> None:
    """整数係数を展開し、元の有理多項式とHorner式の同値を確認する。"""
    numerator = [24, 0, 0, 0, 0, 0, 0]
    terms = [(12, (0, 1)), (8, (0, 1, 2)), (9, (0, 1, 2, 3)), (24, (0, 0, 1, 2, 3, 4))]
    for scale, roots in terms:
        coefficients = [scale]
        for root in roots:
            multiplied = [0] * (len(coefficients) + 1)
            for degree, coefficient in enumerate(coefficients):
                multiplied[degree] -= root * coefficient
                multiplied[degree + 1] += coefficient
            coefficients = multiplied
        for degree, coefficient in enumerate(coefficients):
            numerator[degree] += coefficient
    assert numerator == [24, -50, 663, -1246, 849, -240, 24]
