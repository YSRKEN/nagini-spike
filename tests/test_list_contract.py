"""仕様を実装と呼び出し側の間の契約として利用する。"""

import subprocess
import sys
from pathlib import Path

import pytest

import scripts.check as check
from examples.list_contract import replace_head

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_contract.py"


def test_contract_needs_runtime_preparation() -> None:
    """契約宣言付きの直接実行を動作確認と取り違えない。"""
    with pytest.raises(NotImplementedError, match="overloaded function"):
        replace_head([7], 9)


def test_contract_verifies_and_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """同じソースを検証し、既知の事後条件だけを除いたコピーで具体例を実行する。"""
    source = SOURCE.read_text(encoding="utf-8")
    verified = tmp_path / "verified.py"
    verified.write_text(source, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    code, output = check.run(["-m", "nagini_translation.main", str(verified)], "list_contract")
    assert check.accepted(code, output), output
    assert verified.read_text(encoding="utf-8") == source
    declarations = [
        "    Ensures(Acc(list_pred(values)))\n",
        "    Ensures(len(values) == Old(len(values)))\n",
        "    Ensures(values[0] == value)\n",
    ]
    runtime = source
    for declaration in declarations:
        assert runtime.count(declaration) == 1
        runtime = runtime.replace(declaration, "\n")
    assert runtime.count("Ensures(") == 0
    path = tmp_path / "runtime.py"
    path.write_text(runtime, encoding="utf-8")
    probe = """
import runpy, sys
module = runpy.run_path(sys.argv[1])
for values in ([7], [7, 99], [-3, 10**100]):
    before = values.copy()
    module['replace_head'](values, 9)
    assert values == [9, *before[1:]]
    module['caller'](values, -17)
    assert values == [-16, *before[1:]]
"""
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    assert process.returncode == 0, process.stdout + process.stderr


@pytest.mark.parametrize("mutation", ["wrong_value", "read_only_return", "no_value"])
def test_contract_rejects_target_failure(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """実装の誤りと呼び出し側へ返す契約の不足を区別する。"""
    source = SOURCE.read_text(encoding="utf-8")
    changes = {
        "wrong_value": ("    values[0] = value\n", "    values[0] = value + 1\n"),
        "read_only_return": (
            "    Ensures(Acc(list_pred(values)))\n",
            "    Ensures(Acc(list_pred(values), 1 / 2))\n",
        ),
        "no_value": ("    Ensures(values[0] == value)\n", ""),
    }
    original, replacement = changes[mutation]
    assert source.count(original) == 1
    path = tmp_path / (mutation + ".py")
    path.write_text(source.replace(original, replacement), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    code, output = check.run(["-m", "nagini_translation.main", str(path)], mutation)
    assert code == 1, output
    assert "Verification failed" in output, output
    if mutation == "wrong_value":
        assert "Postcondition of replace_head might not hold." in output, output
        assert "Assertion values[0] == value might not hold." in output, output
    elif mutation == "read_only_return":
        assert "The precondition of values[0] = value + 1 might not hold." in output, output
        assert "insufficient permission" in output, output
    else:
        assert "Assertion values[0] == value might not hold." in output, output
