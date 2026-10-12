"""引数のファイルをN個の別プロセスで同時に検証し、全体の壁時間を測る調査用スクリプト。

使い方（リポジトリのルートで）::

    .venv/Scripts/python.exe docs/research/verification-time/parallel.py ファイル...
"""

import os
import subprocess
import sys
import time
from pathlib import Path

env = dict(os.environ, PYTHONUTF8="1", Z3_EXE=str(Path(sys.prefix, "bin", "z3.exe")))
start = time.time()
procs = [
    (
        f,
        time.time(),
        subprocess.Popen(
            [sys.executable, "-m", "nagini_translation.main", f],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        ),
    )
    for f in sys.argv[1:]
]
for f, t, p in procs:
    out, _ = p.communicate()
    ok = "Verification successful" in out
    print(f"{Path(f).name} done at +{time.time() - start:.1f}s ok={ok}", flush=True)
print(f"ALL wall={time.time() - start:.1f}s for {len(procs)} files")
