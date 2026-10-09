"""契約の除去後も計算と通常のassertが保たれることを確かめる。"""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.extract_absolute import extract

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "absolute_contract.py"


def test_extracted_absolute_runs(tmp_path: Path) -> None:
    """生成したコードを実行し、絶対値と呼び出し側を具体例で確かめる。"""
    extracted = extract(SOURCE.read_text(encoding="utf-8"))
    path = tmp_path / "absolute_runtime.py"
    path.write_text(extracted, encoding="utf-8")
    # 実行用コピーを新しいプロセスで読み、元のモジュールの状態に依存させない。
    probe = (
        "import runpy, sys; m = runpy.run_path(sys.argv[1]); "
        "values = [-(10**100), -17, -1, 0, 1, 17, 10**100]; "
        "assert all(m['absolute'](x) == abs(x) for x in values); "
        "[m['caller'](x) for x in values]"
    )
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    assert process.returncode == 0, process.stdout + process.stderr


def test_extraction_keeps_failure(tmp_path: Path) -> None:
    """抽出が誤実装を修正せず、呼び出し側のassertも消さない。"""
    source = SOURCE.read_text(encoding="utf-8").replace("return -x", "return x")
    path = tmp_path / "absolute_bad.py"
    path.write_text(extract(source), encoding="utf-8")
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy,sys; runpy.run_path(sys.argv[1])['caller'](-1)",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert process.returncode != 0
    assert "AssertionError" in process.stderr


@pytest.mark.parametrize(
    "original,replacement",
    [
        ("Ensures(ResultT(int) >= 0)", "Ensures(ResultT(int) > 0)"),
        ("    Ensures(ResultT(int) >= 0)\n", ""),
        ("return -x", "return ResultT(int)"),
    ],
)
def test_extraction_rejects_changed_contract(original: str, replacement: str) -> None:
    """仕様や検証用記法の使い方が変わったら、黙って除去しない。"""
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count(original) == 1
    with pytest.raises(ValueError):
        extract(source.replace(original, replacement))


@pytest.mark.parametrize("diagnostic", ["Java not found", "Verification failed"])
def test_failed_verification_invalidates_old_copy(
    diagnostic: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """検証失敗や起動失敗の後に、古い成功コピーを使わせない。"""
    import scripts.extract_absolute as extractor

    examples = tmp_path / "examples"
    examples.mkdir()
    (examples / "absolute_contract.py").write_bytes(SOURCE.read_bytes())
    results = tmp_path / "results"
    results.mkdir()
    output = results / "absolute_runtime.py"
    output.write_text("value = 1\n", encoding="utf-8")

    def failed_run(arguments: list[str], label: str) -> tuple[int, str]:
        return 1, diagnostic

    monkeypatch.setattr(extractor, "ROOT", tmp_path)
    monkeypatch.setattr(extractor, "RESULTS", results)
    monkeypatch.setattr(extractor, "run", failed_run)
    assert extractor.main() == 1
    process = subprocess.run(
        [sys.executable, str(output)], capture_output=True, text=True, timeout=10
    )
    assert process.returncode != 0
    assert "RuntimeError" in process.stderr
