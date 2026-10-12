"""Naginiの1回の検証を段階ごとに計時する調査用スクリプト。

``nagini_translation.main`` の関数を差し替えて、各段階の経過時間を標準エラーへ出す。
Z3の子プロセスのCPU時間は、Windowsの``GetProcessTimes``を別スレッドで読んで近似する。

使い方（リポジトリのルートで）::

    .venv/Scripts/python.exe docs/research/verification-time/phase_profile.py FILE.py

環境変数``NOPOLL=1``でZ3のCPU時間の計測を止める（計測自体が時間を伸ばすため）。
"""

import ctypes
import ctypes.wintypes as wt
import os
import sys
import threading
import time

T0 = time.perf_counter()
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("Z3_EXE", os.path.join(sys.prefix, "bin", "z3.exe"))

marks: dict[str, float] = {}
acc: dict[str, float] = {}


def wrap(obj: object, name: str, label: str) -> None:
    """関数を計時つきの関数へ差し替える。累積時間を``acc``へ足す。"""
    orig = getattr(obj, name)

    def inner(*a: object, **k: object) -> object:
        s = time.perf_counter()
        try:
            return orig(*a, **k)
        finally:
            acc[label] = acc.get(label, 0.0) + time.perf_counter() - s

    setattr(obj, name, inner)


# --- Z3子プロセスのCPU時間（Windowsのみ） ---
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE


class PE(ctypes.Structure):
    """PROCESSENTRY32W"""

    _fields_ = [
        ("dwSize", wt.DWORD),
        ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wt.DWORD),
        ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase", wt.LONG),
        ("dwFlags", wt.DWORD),
        ("szExeFile", wt.WCHAR * 260),
    ]


def z3_pids() -> list[int]:
    """自プロセスの子孫にあたるz3.exeのPIDを返す。"""
    snap = k32.CreateToolhelp32Snapshot(2, 0)
    pe = PE()
    pe.dwSize = ctypes.sizeof(PE)
    procs: list[tuple[int, int, str]] = []
    ok = k32.Process32FirstW(snap, ctypes.byref(pe))
    while ok:
        procs.append((pe.th32ProcessID, pe.th32ParentProcessID, pe.szExeFile))
        ok = k32.Process32NextW(snap, ctypes.byref(pe))
    k32.CloseHandle(snap)
    me = os.getpid()
    return [p for p, par, n in procs if n.lower() == "z3.exe" and par == me]


def cpu_of(pid: int) -> float:
    """プロセスのCPU時間（秒）。"""
    h = k32.OpenProcess(0x1000, False, pid)
    if not h:
        return 0.0
    c, e, kt, ut = (wt.FILETIME() for _ in range(4))
    k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut))
    k32.CloseHandle(h)

    def v(f: wt.FILETIME) -> float:
        return ((f.dwHighDateTime << 32) | f.dwLowDateTime) / 1e7

    return v(kt) + v(ut)


z3_cpu: dict[int, float] = {}
stop = threading.Event()


def poll() -> None:
    """z3.exeのCPU時間の最大値をPIDごとに記録する。"""
    while not stop.is_set():
        for pid in z3_pids():
            z3_cpu[pid] = max(z3_cpu.get(pid, 0.0), cpu_of(pid))
        time.sleep(0.05)


def main() -> None:
    """main.pyの本体を、計時を挟んで実行する。"""
    import nagini_translation.main as nm
    from nagini_translation import verifier
    from nagini_translation.analyzer import Analyzer
    from nagini_translation.lib import typeinfo
    from nagini_translation.translator import Translator

    marks["import_done"] = time.perf_counter() - T0
    wrap(typeinfo.TypeInfo, "check", "mypy_typecheck")
    wrap(Analyzer, "process", "analyzer_process")
    wrap(nm, "load_sil_files", "load_builtin_sil")
    wrap(Translator, "translate_program", "translate_program")
    wrap(nm, "translate", "translate_total")
    wrap(nm, "verify", "verify_total")
    wrap(verifier.Silicon, "__init__", "silicon_init")
    wrap(verifier.Silicon, "verify", "silicon_verify")
    if hasattr(verifier, "Carbon"):
        wrap(verifier.Carbon, "__init__", "carbon_init")
        wrap(verifier.Carbon, "verify", "carbon_verify")
    if not os.environ.get("NOPOLL"):
        threading.Thread(target=poll, daemon=True).start()
    orig_jvm = nm.JVM

    def jvm_timed(cp: str) -> object:
        s = time.perf_counter()
        j = orig_jvm(cp)
        marks["jvm_start"] = time.perf_counter() - s
        return j

    nm.JVM = jvm_timed  # type: ignore[misc]
    sys.argv = ["nagini", *sys.argv[1:]]
    code = 0
    try:
        nm.main()
    except SystemExit as e:
        code = int(e.code or 0)
    stop.set()
    marks["total_in_process"] = time.perf_counter() - T0
    print(f"rc={code}", file=sys.stderr)
    for k, v in marks.items():
        print(f"MARK {k}={v:.2f}", file=sys.stderr)
    for k, v in acc.items():
        print(f"ACC {k}={v:.2f}", file=sys.stderr)
    print(f"Z3_CPU {sum(z3_cpu.values()):.2f} pids={len(z3_cpu)}", file=sys.stderr)


if __name__ == "__main__":
    main()
