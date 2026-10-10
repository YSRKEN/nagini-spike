"""辞書更新の一般契約を正例と同契約誤例で照合する。"""

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

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "dict_update.py"
SPECIFICATION = Specification(
    "任意整数辞書の対象値・全旧他キー値・余分キーなし・既存新規の長さ分岐と全権限返却",
    "既存キー・新規キー・空・負整数・巨大整数・長い辞書を有限通常実行で別照合",
)
BODY = "    values[key] = value\n"
MUTATIONS = (
    (
        "wrong_target",
        "    values[key] = value + 1\n",
        "Assertion values[key] == value might not hold.",
        "@28.12--28.50",
    ),
    (
        "destroy",
        "    values[key] = value\n    if key + 1 in values:\n        values[key + 1] += 1\n",
        "Assertion Forall(int, lambda other: Implies(Old(other in values) and other != key, "
        "other in values and values[other] == Old(values[other]))) might not hold.",
        "@30.8--36.9",
    ),
    (
        "extra",
        "    values[key] = value\n    if key + 1 not in values:\n        values[key + 1] = value\n",
        "Assertion Forall(int, lambda other: Implies(other in values, "
        "Old(other in values) or other == key)) might not hold.",
        "@39.8--39.97",
    ),
)


def runtime_function(source: str) -> Callable[[dict[int, int], int, int], None]:
    """照合した五Ensuresを除き、同じ更新本体を通常実行する。"""
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
        "Ensures(Acc(dict_pred(values)))",
        "Ensures(key in values and values[key] == value)",
        "Ensures(Forall(int, lambda other: Implies(Old(other in values) and other != key, "
        "other in values and values[other] == Old(values[other]))))",
        "Ensures(Forall(int, lambda other: Implies(other in values, "
        "Old(other in values) or other == key)))",
        "Ensures(len(values) == Old(len(values)) + (0 if Old(key in values) else 1))",
    )
    assert tuple(ast.dump(node.value) for node in declarations) == tuple(
        ast.dump(ast.parse(expression, mode="eval").body) for expression in expected
    )
    lines = source.splitlines(keepends=True)
    for node in declarations:
        assert node.end_lineno is not None
        for index in range(node.lineno - 1, node.end_lineno):
            lines[index] = "\n"
    runtime = "".join(lines)
    assert "Ensures(" not in runtime
    namespace: dict[str, object] = {}
    exec(compile(runtime, "runtime_dict_update.py", "exec"), namespace)
    return cast(Callable[[dict[int, int], int, int], None], namespace["update_preserving"])


def test_general_update(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """一般保存契約の証明と有限通常実行を別々に確認する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase("dict_update", SPECIFICATION, ExpectedVerification("verified")), SOURCE
    )
    update = runtime_function(SOURCE.read_text(encoding="utf-8-sig"))
    for before in ({}, {0: 7}, {-2: 9, 0: -(10**100)}, dict(enumerate(range(1024)))):
        for key, value in ((0, -5), (-2, 10**100), (2048, -10)):
            values = before.copy()
            update(values, key, value)
            assert values[key] == value
            assert len(values) == len(before) + (key not in before)
            assert all(
                other in values and values[other] == old
                for other, old in before.items()
                if other != key
            )
            assert set(values) == set(before) | {key}


@pytest.mark.parametrize(("name", "replacement", "diagnostic", "position"), MUTATIONS)
def test_mutations(
    name: str,
    replacement: str,
    diagnostic: str,
    position: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """契約を変えず各誤例を狙った事後条件診断と位置で拒否する。"""
    source = SOURCE.read_text(encoding="utf-8-sig")
    mutation = Mutation(BODY, replacement)
    changed = mutation.apply(source)
    assert source.split(BODY)[0] == changed.split(replacement)[0]
    path = tmp_path / ("dict_update_" + name + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    verify_case(
        VerificationCase(
            "dict_update_" + name,
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
    values = {0: 7, 1: 9} if name == "destroy" else {}
    runtime_function(changed)(values, 0, 5)
    assert values == {"wrong_target": {0: 6}, "destroy": {0: 5, 1: 10}, "extra": {0: 5, 1: 5}}[name]
