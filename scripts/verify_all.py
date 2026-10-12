"""features/ の全題材を Nagini で検証し、期待どおりかを確かめて結果表を出す。

使い方::

    uv run --locked python scripts/verify_all.py [--write-readme] [題材ファイル ...]

題材ファイルを省くと features/ の下をすべて検証する。``--write-readme`` を付けると、
README の結果表を差し替える。期待と違う結果が1件でもあれば終了コード1で終わる。
"""

import argparse
import io
import sys
import time
from pathlib import Path
from typing import cast

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.nagini_server import NaginiServer
from scripts.verification_plan import (
    AREAS,
    CheckResult,
    judge,
    plan,
    render_table,
    replace_section,
)

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "features"
README = ROOT / "README.md"
TIMEOUT = 120.0


def discover() -> list[Path]:
    """features/ の題材を、分野の順、分野の中は名前の順に返す。"""
    order = list(AREAS)
    files = [path for path in FEATURES.glob("*/*.py") if not path.name.startswith("_")]
    return sorted(files, key=lambda path: (order.index(path.parent.name), path.name))


def main(arguments: list[str]) -> int:
    """題材を検証し、期待どおりなら 0 を返す。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--write-readme", action="store_true")
    options = parser.parse_args(arguments)
    files = [path.resolve() for path in options.files] or discover()
    plans = {path: plan(path.relative_to(ROOT), path.read_text(encoding="utf-8")) for path in files}

    started = time.perf_counter()
    rows: dict[Path, list[CheckResult]] = {}
    with NaginiServer(ROOT, files[0]) as server:
        for path, checks in plans.items():
            relative = path.relative_to(ROOT)
            rows[relative] = []
            for check in checks:
                reply = server.verify(path, check.select, TIMEOUT)
                outcome, detail = judge(reply.status, reply.text)
                result = CheckResult(check, outcome, reply.seconds, detail)
                rows[relative].append(result)
                mark = "ok" if result.passed else "NG"
                print(
                    f"{mark} {relative.as_posix()} {check.label}: {outcome} ({reply.seconds:.1f}s)",
                    flush=True,
                )
    elapsed = time.perf_counter() - started

    table = render_table(rows)
    print(table)
    failures = [result for results in rows.values() for result in results if not result.passed]
    print(f"題材 {len(rows)} 件、検証 {sum(map(len, rows.values()))} 回、{elapsed:.0f} 秒。")
    if options.write_readme:
        README.write_text(
            replace_section(README.read_text(encoding="utf-8"), table),
            encoding="utf-8",
            newline="\n",
        )
    if failures:
        print(f"期待と違う結果が {len(failures)} 件ある。")
        return 1
    print("すべて期待どおり。")
    return 0


if __name__ == "__main__":
    cast("io.TextIOWrapper[io.BufferedWriter]", sys.stdout).reconfigure(encoding="utf-8")
    cast("io.TextIOWrapper[io.BufferedWriter]", sys.stderr).reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
