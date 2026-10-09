"""作業場所を固定し、通常の検査とNaginiの成功・拒否を確認する。"""

import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def accepted(returncode: int, output: str) -> bool:
    """終了コードと検証成功の診断が揃っているかを返す。"""
    return returncode == 0 and "Verification successful" in output


def rejected(returncode: int, output: str) -> bool:
    """今回壊した非負条件の検証失敗であるかを返す。"""
    return (
        returncode == 1
        and "Verification failed" in output
        and "Assertion result >= 0 might not hold." in output
    )


def timeout_for(arguments: list[str]) -> int:
    """個々の検証と、それらをまとめて実行するテストの制限を返す。"""
    return 600 if arguments[:2] == ["-m", "pytest"] else 90


def run(arguments: list[str], label: str) -> tuple[int, str]:
    """タイムアウトを設け、プロジェクト内だけで検査を実行する。"""
    print(label, flush=True)
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    if "nagini_translation.main" in arguments:
        z3_name = "z3.exe" if os.name == "nt" else "z3"
        z3_path = Path(sys.prefix) / "bin" / z3_name
        if not z3_path.is_file():
            raise FileNotFoundError("仮想環境に同梱されたZ3がありません。")
        environment["Z3_EXE"] = str(z3_path)
    process = subprocess.run(
        [sys.executable, *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_for(arguments),
        check=False,
    )
    output = process.stdout + process.stderr
    (RESULTS / (label + ".log")).write_bytes(output.encode("utf-8"))
    print(output, end="" if output.endswith("\n") else "\n", flush=True)
    return process.returncode, output


def main() -> int:
    """通常の検査と、正しい実装・誤実装の検証を順に実行する。"""
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "summary.json").write_bytes(b'{"status": "running"}')
    checks = [
        (["-m", "ruff", "check", "examples", "scripts", "tests"], "lint"),
        (["-m", "ruff", "format", "--check", "examples", "scripts", "tests"], "format"),
        (["-m", "pyright"], "types"),
        (["-m", "pytest", "-q", "tests"], "tests"),
    ]
    for arguments, label in checks:
        returncode, _ = run(arguments, label)
        if returncode != 0:
            return 1

    returncode, output = run(["-m", "nagini_translation.main", "examples/absolute.py"], "absolute")
    if not accepted(returncode, output):
        print("正しい実装の検証成功を確認できません。")
        return 1

    source = (ROOT / "examples/absolute.py").read_text(encoding="utf-8")
    if source.count("result = -x") != 1:
        print("誤実装を作る置換箇所が変わっています。")
        return 1
    broken = source.replace("result = -x", "result = x")
    (RESULTS / "absolute_bad.py").write_bytes(broken.encode("utf-8"))
    returncode, output = run(
        ["-m", "nagini_translation.main", "results/absolute_bad.py"], "absolute_bad"
    )
    if not rejected(returncode, output):
        print("誤実装が狙った条件で拒否されたことを確認できません。")
        return 1

    summary = {"absolute": "verified", "absolute_bad": "rejected_at_nonnegative_assertion"}
    (RESULTS / "summary.json").write_bytes(
        (json.dumps(summary, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    print("すべての検査に成功しました。")
    return 0


if __name__ == "__main__":
    cast("io.TextIOWrapper[io.BufferedWriter]", sys.stdout).reconfigure(encoding="utf-8")
    cast("io.TextIOWrapper[io.BufferedWriter]", sys.stderr).reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (OSError, subprocess.TimeoutExpired) as error:
        print("検査を完了できません: " + str(error), file=sys.stderr)
        raise SystemExit(1) from error
