"""任意長リストの末尾追加契約を正例と独立誤例で検査する。"""

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
    "全書き込み権限を返し、任意長整数リストの長さ1増・旧全要素保存・新末尾一致",
    "同一ソースの既知Ensures行だけを除き、空・負数・重複・巨大整数・長い列で照合",
)
SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_append.py"
BODY = "    values.append(value)\n"
MUTATIONS = (
    ("extra", "    values.append(value)\n    values.append(value)\n", "len(values) == Old(len(values)) + 1"),
    ("destroy", "    if len(values) > 0:\n        values[0] += 1\n    values.append(value)\n", "Forall(int, lambda i: Implies(0 <= i and i < Old(len(values)), values[i] == Old(ToSeq(values))[i]))"),
    ("wrong_tail", "    values.append(value + 1)\n", "values[len(values) - 1] == value"),
)


def runtime_function(source: str) -> Callable[[list[int], int], None]:
    """照合した四つの事後条件宣言だけを除き、計算本体を実行する。"""
    declarations = [line for line in source.splitlines() if line.strip().startswith("Ensures(")]
    assert len(declarations) == 4
    runtime = "\n".join(line for line in source.splitlines() if line not in declarations)
    assert "Ensures(" not in runtime
    namespace: dict[str, object] = {}
    exec(compile(runtime, "runtime_list_append.py", "exec"), namespace)
    return cast(Callable[[list[int], int], None], namespace["append_preserving"])


def test_correct_append(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般契約の成功と有限例の通常実行を別々に確認する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(VerificationCase("list_append", SPECIFICATION, ExpectedVerification("verified")), SOURCE)
    append = runtime_function(SOURCE.read_text(encoding="utf-8"))
    for before in ([], [7], [-2, -2, 0, 10**100], list(range(1024))):
        for value in (-10**100, 0, 9):
            values = before.copy()
            append(values, value)
            assert len(values) == len(before) + 1
            assert values[:-1] == before
            assert values[-1] == value


@pytest.mark.parametrize(("name", "replacement", "condition"), MUTATIONS)
def test_independent_mutations(
    name: str, replacement: str, condition: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """同じ前提と事後条件を保ち、各性質だけを壊した誤例を拒否する。"""
    source = SOURCE.read_text(encoding="utf-8")
    mutation = Mutation(BODY, replacement)
    changed = mutation.apply(source)
    assert source.split(BODY)[0] == changed.split(replacement)[0]
    path = tmp_path / ("list_append_" + name + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "list_append_" + name,
            SPECIFICATION,
            ExpectedVerification("proof_failure", (
                "Postcondition of append_preserving might not hold.",
                "Assertion " + condition + " might not hold.",
            )),
            mutation,
        ),
        path,
    )
    values = [7, -2]
    runtime_function(changed)(values, 9)
    assert values == {"extra": [7, -2, 9, 9], "destroy": [8, -2, 9], "wrong_tail": [7, -2, 10]}[name]
