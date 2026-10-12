"""examples/*.py をそれぞれ別プロセス（コールド）で1回ずつ検証し、壁時間を表にする調査用スクリプト。

使い方（リポジトリのルートで）::

    .venv/Scripts/python.exe docs/research/verification-time/cold_all.py [ファイル名...]
"""

import os
import subprocess
import sys
import time
from pathlib import Path

env = dict(os.environ, PYTHONUTF8="1", Z3_EXE=str(Path(sys.prefix, "bin", "z3.exe")))
files = sys.argv[1:] or sorted(
    str(p) for p in Path("examples").glob("*.py") if p.name != "__init__.py"
)
for f in files:
    s = time.time()
    p = subprocess.run(
        [sys.executable, "-m", "nagini_translation.main", f],
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
    )
    wall = time.time() - s
    out = p.stdout + p.stderr
    took = next(
        (ln.split()[2] for ln in out.splitlines() if ln.startswith("Verification took")), "-"
    )
    res = "ok" if "Verification successful" in out else "fail"
    lines = len(Path(f).read_text(encoding="utf-8").splitlines())
    print(f"{Path(f).name}\tlines={lines}\twall={wall:.1f}\ttook={took}\t{res}", flush=True)
