"""Optional戻り契約と呼び出し側を共通形式で検査する。"""

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

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "optional_return.py"
SPECIFICATION = Specification(
    "任意intからNone iff 負、非Noneなら入力一致。呼出側は欠損0、非負入力+1",
    "同じソースの照合済み事後条件のみ除去して負数・零・正数・巨大整数を実行",
)
CONDITIONS = (
    "    Ensures((Result() is None) == (value < 0))\n",
    "    Ensures(Result() is None or Result() == value)\n",
    "    Ensures(value >= 0 or Result() == 0)\n",
    "    Ensures(value < 0 or Result() == value + 1)\n",
)
MUTATIONS = (
    ("negative", "        return None\n", "        return value\n"),
    ("nonnegative", "    return value\n", "    return None\n"),
    ("value", "    return value\n", "    return value + 1\n"),
)


def runtime_functions(source: str) -> tuple[Callable[[int], int | None], Callable[[int], int]]:
    """照合した契約のみを取り除いて同じ二つの関数を実行する。"""
    for condition in CONDITIONS:
        assert source.count(condition) == 1
        source = source.replace(condition, "\n")
    assert "Ensures(" not in source
    namespace: dict[str, object] = {}
    exec(compile(source, "runtime_optional_return.py", "exec"), namespace)
    return (
        cast(Callable[[int], int | None], namespace["nonnegative_or_none"]),
        cast(Callable[[int], int], namespace["increment_nonnegative"]),
    )


def test_correct_optional_return(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般証明成功と通常実行の具体例を別々に確認する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("optional_return", SPECIFICATION, ExpectedVerification("verified")),
        SOURCE,
    )
    select, increment = runtime_functions(SOURCE.read_text(encoding="utf-8-sig"))
    for value in (-(10**100), -2, -1, 0, 1, 2, 10**100):
        assert select(value) == (None if value < 0 else value)
        assert increment(value) == (0 if value < 0 else value + 1)


@pytest.mark.parametrize(("name", "original", "replacement"), MUTATIONS)
def test_return_mutations(
    name: str,
    original: str,
    replacement: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """契約を保持し返却分岐だけを壊して指定事後条件の拒否を確認する。"""
    source = SOURCE.read_text(encoding="utf-8-sig")
    mutation = Mutation(original, replacement)
    changed = mutation.apply(source)
    for condition in CONDITIONS:
        assert changed.count(condition) == 1
    path = tmp_path / ("optional_return_" + name + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    diagnostic = (
        "Assertion Result() is None or Result() == value might not hold."
        if name == "value"
        else "Assertion (Result() is None) == (value < 0) might not hold."
    )
    position = "22.12--22.47" if name == "value" else "21.12--21.46"
    verify_case(
        VerificationCase(
            "optional_return_" + name,
            SPECIFICATION,
            ExpectedVerification(
                "proof_failure",
                (
                    "Postcondition of nonnegative_or_none might not hold.",
                    diagnostic,
                    "optional_return_" + name + ".py@" + position,
                ),
            ),
            mutation,
        ),
        path,
    )
