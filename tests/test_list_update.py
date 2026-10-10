"""任意有効添字更新の一般契約を共通ケースで照合する。"""

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

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_update.py"
SPECIFICATION = Specification(
    "任意整数リストの有効添字更新で対象値・長さ不変・全他要素保存・全権限返却",
    "単一・先頭・末尾・負整数・巨大整数・長い列の有限通常実行を別照合",
)
BODY = "    values[index] = value\n"
MUTATIONS = (
    (
        "wrong_target",
        "    values[index] = value + 1\n",
        "Assertion values[index] == value might not hold.",
        "@31.12--31.34",
    ),
    (
        "destroy",
        "    values[index] = value\n    if len(values) > 1:\n"
        "        other = (index + 1) % len(values)\n        values[other] += 1\n",
        "Assertion Forall(int, lambda other: Implies(0 <= other and other < Old(len(values)) "
        "and (other != index), values[other] == Old(ToSeq(values))[other])) might not hold.",
        "@33.8--39.9",
    ),
    (
        "extra",
        "    values[index] = value\n    values.append(value)\n",
        "Assertion len(values) == Old(len(values)) might not hold.",
        "@30.12--30.43",
    ),
)


def runtime_function(source: str) -> Callable[[list[int], int, int], None]:
    """照合した四Ensuresを除き同じ計算本体を通常実行する。"""
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    declarations = [
        node
        for node in function.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "Ensures"
    ]
    expected = (
        "Ensures(Acc(list_pred(values)))",
        "Ensures(len(values) == Old(len(values)))",
        "Ensures(values[index] == value)",
        "Ensures(Forall(int, lambda other: Implies(0 <= other and other < Old(len(values)) "
        "and other != index, values[other] == Old(ToSeq(values))[other])))",
    )
    assert tuple(ast.dump(node.value) for node in declarations) == tuple(
        ast.dump(ast.parse(expression, mode="eval").body) for expression in expected
    )
    lines = source.splitlines(keepends=True)
    for node in declarations:
        assert node.end_lineno is not None
        for line in range(node.lineno - 1, node.end_lineno):
            lines[line] = "\n"
    runtime = "".join(lines)
    assert "Ensures(" not in runtime
    namespace: dict[str, object] = {}
    exec(compile(runtime, "runtime_list_update.py", "exec"), namespace)
    return cast(Callable[[list[int], int, int], None], namespace["update_preserving"])


def test_general_update(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般静的証明と有限通常実行を分けて確認する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("list_update", SPECIFICATION, ExpectedVerification("verified")), SOURCE
    )
    update = runtime_function(SOURCE.read_text(encoding="utf-8-sig"))
    for before in ([7], [-2, -2, 0, 10**100], list(range(1024))):
        for index in sorted({0, len(before) // 2, len(before) - 1}):
            for value in (-(10**100), 0, 9):
                values = before.copy()
                update(values, index, value)
                assert values[index] == value
                assert len(values) == len(before)
                assert all(values[j] == old for j, old in enumerate(before) if j != index)


@pytest.mark.parametrize(("name", "replacement", "diagnostic", "position"), MUTATIONS)
def test_mutations(
    name: str,
    replacement: str,
    diagnostic: str,
    position: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """契約を保ち各誤例を狙った全文診断と位置で拒否する。"""
    source = SOURCE.read_text(encoding="utf-8-sig")
    mutation = Mutation(BODY, replacement)
    changed = mutation.apply(source)
    assert source.split(BODY)[0] == changed.split(replacement)[0]
    path = tmp_path / ("list_update_" + name + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "list_update_" + name,
            SPECIFICATION,
            ExpectedVerification(
                "proof_failure",
                (
                    "Postcondition of update_preserving might not hold.",
                    diagnostic,
                    path.name + position,
                ),
            ),
            mutation,
        ),
        path,
    )
    values = [7, -2]
    runtime_function(changed)(values, 0, 9)
    assert values == {"wrong_target": [10, -2], "destroy": [9, -1], "extra": [9, -2, 9]}[name]
