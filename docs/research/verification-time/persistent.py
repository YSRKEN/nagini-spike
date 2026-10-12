"""同じJVMで複数ファイルを続けて検証し、1ファイルごとの時間を測る調査用スクリプト。

Naginiの``--server``モードの本体は、JVMとビルトインSilファイルを1度だけ読み込み、
要求のたびに``translate_and_verify``を呼ぶループである（``nagini_translation/main.py``）。
このスクリプトはZeroMQの送受信だけを省いて、同じ呼び出しを繰り返す。

使い方（リポジトリのルートで）::

    .venv/Scripts/python.exe docs/research/verification-time/persistent.py [--viper-server] \
        [--verifier carbon] ファイル...
"""

import os
import sys
import time

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("Z3_EXE", os.path.join(sys.prefix, "bin", "z3.exe"))
T0 = time.perf_counter()


def main() -> None:
    """引数のうち``.py``だけをファイルとして扱い、残りをNaginiのオプションへ渡す。"""
    import nagini_translation.main as nm

    files = [a for a in sys.argv[1:] if a.endswith(".py")]
    opts = [a for a in sys.argv[1:] if not a.endswith(".py")]
    orig = nm.translate_and_verify

    def loop(python_file: str, jvm: object, args: object, *a: object, **k: object) -> bool:
        print(f"startup(import+JVM) {time.perf_counter() - T0:.2f}s", flush=True)
        ok = True
        for f in files:
            s = time.perf_counter()
            ok = orig(f, jvm, args, *a, **k) and ok
            print(f"PERSISTENT {os.path.basename(f)} {time.perf_counter() - s:.2f}s", flush=True)
        return ok

    nm.translate_and_verify = loop
    sys.argv = ["nagini", *opts, files[0]]
    nm.main()


if __name__ == "__main__":
    main()
