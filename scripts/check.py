"""リポジトリの検査をまとめて流す。

使い方::

    uv run --locked python scripts/check.py

lint・整形・型検査・一括実行のテスト・全題材の検証を順に流し、どれかが落ちたらそこで止める。
README の結果表は書き換えない。書き換えるときは ``scripts/verify_all.py --write-readme`` を使う。
"""

import io
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["features", "scripts", "tests"]
STEPS = [
    ("lint", ["-m", "ruff", "check", *TARGETS]),
    ("format", ["-m", "ruff", "format", "--check", *TARGETS]),
    ("types", ["-m", "pyright"]),
    ("tests", ["-m", "pytest", "-q"]),
    ("verify", ["scripts/verify_all.py"]),
]


def main() -> int:
    """検査を順に流し、すべて通れば 0 を返す。"""
    for label, arguments in STEPS:
        print(f"== {label}", flush=True)
        started = time.perf_counter()
        returncode = subprocess.call([sys.executable, *arguments], cwd=ROOT)
        print(f"== {label}: {time.perf_counter() - started:.0f} 秒", flush=True)
        if returncode != 0:
            print(f"{label} が通らなかった。")
            return 1
    print("すべての検査が通った。")
    return 0


if __name__ == "__main__":
    cast("io.TextIOWrapper[io.BufferedWriter]", sys.stdout).reconfigure(encoding="utf-8")
    raise SystemExit(main())
