"""Optionalの一般契約を正例と独立した分岐誤例で検査する。"""

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
    "制限のないOptional[int]全体でNoneなら0、整数ならvalue+1。型絞り込み後の加算",
    "同一ソースの照合したEnsures二行だけを除き、None・負数・0・巨大整数で通常実行",
)
SOURCE = Path(__file__).resolve().parents[1] / "examples" / "optional_narrow.py"
BODY = "    if value is None:\n        return 0\n    return value + 1\n"
MUTATIONS = (
    (
        "wrong_none",
        "        return 0\n",
        "        return 1\n",
        "value is not None or Result() == 0",
    ),
    (
        "wrong_int",
        "    return value + 1\n",
        "    return value\n",
        "value is None or Result() == value + 1",
    ),
)


def runtime_function(source: str) -> Callable[[int | None], int]:
    """照合した二つの事後条件だけを除き、同じ計算本体を実行する。"""
    runtime = source
    for condition in (
        "    Ensures(value is not None or Result() == 0)\n",
        "    Ensures(value is None or Result() == value + 1)\n",
    ):
        assert runtime.count(condition) == 1
        runtime = runtime.replace(condition, "\n")
    assert "Ensures(" not in runtime
    namespace: dict[str, object] = {}
    exec(compile(runtime, "runtime_optional_narrow.py", "exec"), namespace)
    return cast(Callable[[int | None], int], namespace["increment_or_default"])


def test_correct_optional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """任意入力の証明成功と有限具体例の通常実行を分けて確認する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("optional_narrow", SPECIFICATION, ExpectedVerification("verified")),
        SOURCE,
    )
    calculate = runtime_function(SOURCE.read_text(encoding="utf-8-sig"))
    for value in (None, -(10**100), -2, -1, 0, 1, 10**100):
        assert calculate(value) == (0 if value is None else value + 1)


@pytest.mark.parametrize(("name", "original", "replacement", "condition"), MUTATIONS)
def test_independent_mutations(
    name: str,
    original: str,
    replacement: str,
    condition: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """同じ契約を保ち各分岐の返却値だけを壊し狙った事後条件で拒否する。"""
    source = SOURCE.read_text(encoding="utf-8-sig")
    assert BODY in source
    mutation = Mutation(original, replacement)
    changed = mutation.apply(source)
    assert source.split(BODY)[0] == changed.split("    if value is None:\n")[0]
    path = tmp_path / ("optional_" + name + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "optional_" + name,
            SPECIFICATION,
            ExpectedVerification(
                "proof_failure",
                (
                    "Postcondition of increment_or_default might not hold.",
                    "Assertion " + condition + " might not hold.",
                ),
            ),
            mutation,
        ),
        path,
    )
    calculate = runtime_function(changed)
    assert calculate(None) == (1 if name == "wrong_none" else 0)
    assert calculate(7) == (7 if name == "wrong_int" else 8)
