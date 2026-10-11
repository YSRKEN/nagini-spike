"""空非空の一般結果契約と呼び出し側を検査する。"""

import ast
from pathlib import Path
from typing import Callable, cast

import pytest

import scripts.check as check
from scripts.verification_cases import (
    ExpectedVerification,
    Specification,
    VerificationCase,
    verify_case,
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_empty.py"
SPECIFICATION = Specification(
    "任意整数リストの空非空bool同値、全権限・長さ・内容保存、caller実先頭読取",
    "空・単一・複数の負零正整数と任意defaultの有限通常実行を別照合",
)


def test_correct_list_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般結果契約と先頭を実読取するcallerの証明成功を要求する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("list_empty", SPECIFICATION, ExpectedVerification("verified")), SOURCE
    )

    predicate, read = runtime_functions(SOURCE.read_text(encoding="utf-8-sig"))
    cases: tuple[list[int], ...] = (
        [],
        [0],
        [-7],
        [9],
        [-4, 0, 7],
        [10**100, -(10**100)],
        list(range(1024)),
    )
    for values in cases:
        before = values.copy()
        assert predicate(values) == (len(before) > 0)
        for default in (-8, 0, 11):
            assert read(values, default) == (before[0] if before else default)
            assert values == before


def runtime_functions(
    source: str,
) -> tuple[Callable[[list[int]], bool], Callable[[list[int], int], int]]:
    """固定宣言だけを除き同じ実装を通常実行する。"""
    tree = ast.parse(source)
    removed: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            statements: list[ast.stmt] = []
            for statement in node.body:
                if (
                    isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Call)
                    and isinstance(statement.value.func, ast.Name)
                    and statement.value.func.id in ("Requires", "Ensures")
                ):
                    removed.append(statement.value.func.id)
                else:
                    statements.append(statement)
            node.body = statements
    assert removed.count("Requires") == 2
    assert removed.count("Ensures") == 9
    namespace: dict[str, object] = {}
    exec(compile(tree, "runtime_list_empty.py", "exec"), namespace)
    return (
        cast(Callable[[list[int]], bool], namespace["has_head"]),
        cast(Callable[[list[int], int], int], namespace["read_or_default"]),
    )


@pytest.mark.parametrize("name", ("empty", "nonempty"))
def test_list_empty_mutations(name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """空側または非空側だけの誤返却を同じ事後条件で拒否する。"""
    from scripts.verification_cases import Mutation

    source = SOURCE.read_text(encoding="utf-8-sig")
    replacement = (
        "    if len(values) == 0:\n        return True\n    return len(values) > 0\n"
        if name == "empty"
        else "    if len(values) > 0:\n        return False\n    return len(values) > 0\n"
    )
    mutation = Mutation("    return len(values) > 0\n", replacement)
    path = tmp_path / ("list_empty_" + name + ".py")
    path.write_text(mutation.apply(source), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "list_empty_" + name,
            SPECIFICATION,
            ExpectedVerification(
                "proof_failure",
                (
                    "Postcondition of has_head might not hold.",
                    "Assertion Result() == (len(values) > 0) might not hold.",
                    "list_empty_" + name + ".py@32.12--32.41",
                ),
            ),
            mutation,
        ),
        path,
    )
    output = (tmp_path / ("list_empty_" + name + ".log")).read_text(encoding="utf-8")
    assert output.count("Postcondition of has_head might not hold.") == 1
    predicate, _ = runtime_functions(mutation.apply(source))
    for values in ([], [0], [-4, 9]):
        before = values.copy()
        expected = name == "empty"
        assert predicate(values) == expected
        assert values == before


def test_list_empty_missing_relation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """結果と非空の対応を欠くとcaller先頭アクセスを証明できない。"""
    from scripts.verification_cases import Mutation

    mutation = Mutation("    Ensures(Result() == (len(values) > 0))\n", "")
    path = tmp_path / "list_empty_missing_relation.py"
    path.write_text(mutation.apply(SOURCE.read_text(encoding="utf-8-sig")), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "list_empty_missing_relation",
            SPECIFICATION,
            ExpectedVerification(
                "proof_failure",
                (
                    "The precondition of values[0] might not hold.",
                    "list_empty_missing_relation.py@58.15--58.24",
                    "found at list_empty_missing_relation.py@57.7--57.12",
                ),
            ),
            mutation,
        ),
        path,
    )
