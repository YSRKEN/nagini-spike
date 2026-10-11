"""時間切れ時の子孫回収と独立プロセスの非干渉を確認する。"""

import ctypes
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

from scripts import check


@pytest.mark.parametrize(
    "inherited,early_exit", [(False, False), (True, False), (True, True), (False, True)]
)
@pytest.mark.skipif(os.name != "nt", reason="Windows Job Objectの限定検証")
def test_cleans_descendants_and_keeps_unrelated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, inherited: bool, early_exit: bool
) -> None:
    """親子孫を回収し、独立対照を維持して原出力を保存する。"""
    fixture = tmp_path / "tree.py"
    fixture.write_text(
        "import ctypes, json, os, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "folder, depth = Path(sys.argv[1]), int(sys.argv[2])\n"
        "api = ctypes.WinDLL('kernel32', use_last_error=True)\n"
        "api.GetCurrentProcess.restype = ctypes.c_void_p\n"
        "api.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p]*4\n"
        "times = [ctypes.c_ulonglong() for _ in range(4)]\n"
        "assert api.GetProcessTimes(api.GetCurrentProcess(), *map(ctypes.byref, times))\n"
        "(folder / (str(depth) + '.pid')).write_text(json.dumps("
        "{'pid': os.getpid(), 'created': times[0].value}))\n"
        "print('synthetic stdout', flush=True)\n"
        "print('synthetic stderr', file=sys.stderr, flush=True)\n"
        "if depth: subprocess.Popen([sys.executable, __file__, str(folder), str(depth-1)], "
        f"stdout={'None' if inherited else 'subprocess.DEVNULL'}, "
        f"stderr={'None' if inherited else 'subprocess.DEVNULL'})\n"
        "if depth == 2:\n"
        "    while not (folder / '0.pid').exists(): time.sleep(0.01)\n"
        f"time.sleep({'0 if depth == 2 else 60' if early_exit else '60'})\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check, "RESULTS", tmp_path)

    def short_timeout(_arguments: list[str]) -> int:
        return 3

    monkeypatch.setattr(check, "timeout_for", short_timeout)
    control = subprocess.Popen(
        [cast(str, getattr(sys, "_base_executable")), "-c", "import time; time.sleep(60)"]
    )
    identities: list[int] = []
    try:
        if early_exit and not inherited:
            returncode, _output = check.run([str(fixture), str(tmp_path), "2"], "synthetic_timeout")
            assert returncode == 0
        else:
            with pytest.raises(subprocess.TimeoutExpired):
                check.run([str(fixture), str(tmp_path), "2"], "synthetic_timeout")
        identities = [int(json.loads(path.read_text())["pid"]) for path in tmp_path.glob("*.pid")]
        assert len(identities) == 3
        assert control.poll() is None
        # tasklistは名前を終了条件に使わず、この合成試験のPIDだけ照合する。
        for identity in identities:
            observed = subprocess.run(
                ["tasklist", "/FI", f"PID eq {identity}", "/FO", "CSV", "/NH"],
                capture_output=True,
                timeout=10,
                check=True,
            ).stdout
            assert f'"{identity}"'.encode() not in observed
        log = (tmp_path / "synthetic_timeout.log").read_text(encoding="utf-8")
        assert "synthetic stdout" in log
        assert "synthetic stderr" in log
        if not (early_exit and not inherited):
            assert "timeout" in log
            assert not check.accepted(1, log)
            assert not check.rejected(1, log)
    finally:
        control.terminate()
        control.wait(timeout=10)
        # 合成プロセスの開始時刻と保持ハンドルを照合し、PID再利用を除外する。
        for path in tmp_path.glob("*.pid"):
            marker: dict[str, int] = json.loads(path.read_text())
            _cleanup_fixture(marker["pid"], marker["created"])


def _cleanup_fixture(identity: int, created: int) -> None:
    api: Any = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    api.OpenProcess.restype = ctypes.c_void_p
    api.GetProcessTimes.argtypes = [ctypes.c_void_p] * 5
    api.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    api.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = api.OpenProcess(0x100401, False, identity)
    if not handle:
        return
    try:
        times = [ctypes.c_ulonglong() for _ in range(4)]
        if api.GetProcessTimes(handle, *map(ctypes.byref, times)) and times[0].value == created:
            api.TerminateProcess(handle, 1)
            assert api.WaitForSingleObject(handle, 5000) == 0
    finally:
        api.CloseHandle(handle)


def test_run_success_preserves_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """正常終了のコードと標準出力・標準エラーを保存する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    result, output = check.run(
        ["-c", "import sys; print('normal stdout'); print('normal stderr', file=sys.stderr)"],
        "synthetic_success",
    )
    assert result == 0
    assert "normal stdout" in output
    assert "normal stderr" in output
    assert (tmp_path / "synthetic_success.log").read_bytes().decode("utf-8") == output


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Objectの限定検証")
def test_assignment_failure_never_starts_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """所属設定に失敗したときは検査本体を起動しない。"""
    from scripts.process_runner import WindowsJob

    marker = tmp_path / "unexpected-start.txt"

    def deny(_job: WindowsJob, _process: subprocess.Popen[bytes]) -> None:
        raise OSError("synthetic assignment failure")

    monkeypatch.setattr(WindowsJob, "assign", deny)
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    with pytest.raises(OSError, match="synthetic assignment failure"):
        check.run(["-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"], "denied")
    assert not marker.exists()
