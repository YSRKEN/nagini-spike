"""不在キーの一般契約と安全な呼び出し側を検査する。"""

import ast
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

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "dict_missing.py"
SPECIFICATION = Specification(
    "任意整数辞書とキー、None iff 不在、存在値一致、全内容長さ権限保存、caller辞書読取",
    "空辞書・不在・存在零負正の有限通常実行を一般証明と別に照合",
)
MUTATIONS = (
    ("present", "    return values[key]\n\n\n", "    return None\n\n\n"),
    ("missing", "        return None\n", "        return 0\n"),
    ("value", "    return values[key]\n\n\n", "    return values[key] + 1\n\n\n"),
)


def runtime_functions(
    source: str,
) -> tuple[Callable[[dict[int, int], int], int | None], Callable[[dict[int, int], int, int], int]]:
    """固定契約の宣言だけを除去し同じ実装の有限例を実行する。"""
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
    assert removed.count("Ensures") == 12
    namespace: dict[str, object] = {}
    exec(compile(tree, "runtime_dict_missing.py", "exec"), namespace)
    return (
        cast(Callable[[dict[int, int], int], int | None], namespace["lookup"]),
        cast(Callable[[dict[int, int], int, int], int], namespace["read_or_default"]),
    )


def test_correct_dict_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般契約と呼び出し側の成功を有限通常実行と分けて要求する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("dict_missing", SPECIFICATION, ExpectedVerification("verified")),
        SOURCE,
    )
    lookup, read = runtime_functions(SOURCE.read_text(encoding="utf-8-sig"))
    cases: tuple[tuple[dict[int, int], int], ...] = (
        ({}, 0),
        ({1: 0}, 1),
        ({1: -4}, 1),
        ({1: 7}, 1),
        ({1: 7}, 2),
        ({-(10**100): 10**100, 0: -1}, -(10**100)),
        ({-(10**100): 10**100, 0: -1}, 10**100),
    )
    for values, key in cases:
        before = values.copy()
        assert lookup(values, key) == (before[key] if key in before else None)
        for default in (-8, 0, 11):
            assert read(values, key, default) == (before[key] if key in before else default)
            assert values == before


@pytest.mark.parametrize(("name", "original", "replacement"), MUTATIONS)
def test_dict_missing_mutations(
    name: str,
    original: str,
    replacement: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """同一契約の三つの誤返却を指定診断と位置で拒否する。"""
    source = SOURCE.read_text(encoding="utf-8-sig")
    mutation = Mutation(original, replacement)
    changed = mutation.apply(source)
    before = ast.parse(source)
    after = ast.parse(changed)
    for left, right in zip(before.body, after.body, strict=True):
        if isinstance(left, ast.FunctionDef) and isinstance(right, ast.FunctionDef):
            assert ast.dump(ast.Module(body=left.body[:-2], type_ignores=[])) == ast.dump(
                ast.Module(body=right.body[:-2], type_ignores=[])
            )
    path = tmp_path / ("dict_missing_" + name + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    diagnostic = (
        "Assertion Result() is None or Result() == values[key] might not hold."
        if name == "value"
        else "Assertion (Result() is None) == (key not in values) might not hold."
    )
    position = "43.12--43.55" if name == "value" else "42.12--42.53"
    verify_case(
        VerificationCase(
            "dict_missing_" + name,
            SPECIFICATION,
            ExpectedVerification(
                "proof_failure",
                (
                    "Postcondition of lookup might not hold.",
                    diagnostic,
                    "dict_missing_" + name + ".py@" + position,
                ),
            ),
            mutation,
        ),
        path,
    )
    output = (tmp_path / ("dict_missing_" + name + ".log")).read_text(encoding="utf-8")
    assert output.count("Postcondition of lookup might not hold.") == 1
    lookup, _ = runtime_functions(changed)
    values = {} if name == "missing" else {1: -4}
    assert lookup(values, 1) != (values[1] if 1 in values else None)
