"""検査ごとの子孫プロセスを起動境界から隔離して回収する。"""

import ctypes
import os
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

# 所属設定より前には検査を起動しない。仮想環境ラッパーも設定後に起動する。
_BOOTSTRAP = (
    "import subprocess,sys; "
    "sys.stdin.buffer.read(1); "
    "sys.exit(subprocess.call(sys.argv[1:], stdin=subprocess.DEVNULL))"
)


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_longlong),
        ("job_time", ctypes.c_longlong),
        ("flags", ctypes.c_ulong),
        ("minimum", ctypes.c_size_t),
        ("maximum", ctypes.c_size_t),
        ("active_limit", ctypes.c_ulong),
        ("affinity", ctypes.c_size_t),
        ("priority", ctypes.c_ulong),
        ("scheduling", ctypes.c_ulong),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in ("r", "w", "o", "rb", "wb", "ob")]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("basic", _BasicLimits),
        ("io", _IoCounters),
        ("process_memory", ctypes.c_size_t),
        ("job_memory", ctypes.c_size_t),
        ("peak_process", ctypes.c_size_t),
        ("peak_job", ctypes.c_size_t),
    ]
    basic: _BasicLimits


class _Accounting(ctypes.Structure):
    _fields_ = [
        ("user", ctypes.c_longlong),
        ("kernel", ctypes.c_longlong),
        ("period_user", ctypes.c_longlong),
        ("period_kernel", ctypes.c_longlong),
        ("faults", ctypes.c_ulong),
        ("total", ctypes.c_ulong),
        ("active", ctypes.c_ulong),
        ("terminated", ctypes.c_ulong),
    ]
    active: int


class WindowsJob:
    """単一検査専用Jobのネイティブハンドルを所有する。"""

    def __init__(self) -> None:
        # ctypesの関数型は実行時にargtypesで固定する。
        self.api: Any = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        self.api.CreateJobObjectW.restype = ctypes.c_void_p
        self.api.SetInformationJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_ulong,
        ]
        self.api.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.api.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        self.api.QueryInformationJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_void_p,
        ]
        self.api.CloseHandle.argtypes = [ctypes.c_void_p]
        self.handle: int = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = _ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def assign(self, process: subprocess.Popen[bytes]) -> None:
        """起動待ちの親を所属させ、PID再利用のために列挙を使わない。"""
        # Popenが保持する元プロセスのハンドルを使い、PID再利用を排除する。
        handle = int(getattr(process, "_handle"))
        if not self.api.AssignProcessToJobObject(self.handle, handle):
            raise ctypes.WinError(ctypes.get_last_error())

    def terminate_and_wait(self) -> None:
        """Jobの子孫だけを終了し、全所属プロセスの終了を待つ。"""
        if not self.api.TerminateJobObject(self.handle, 1):
            raise ctypes.WinError(ctypes.get_last_error())
        deadline = time.monotonic() + 5
        while True:
            accounting = _Accounting()
            if not self.api.QueryInformationJobObject(
                self.handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            if accounting.active == 0:
                return
            if time.monotonic() >= deadline:
                raise OSError("検査Jobの子孫プロセスを5秒以内に回収できませんでした。")
            time.sleep(0.01)

    def close(self) -> None:
        """検査専用Jobのハンドルを閉じる。"""
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = 0


def run_captured(
    command: list[str], *, cwd: Path, env: Mapping[str, str], timeout: float
) -> subprocess.CompletedProcess[str]:
    """出力を捕捉し、Windowsでは専用Job内で検査を実行する。"""
    if os.name != "nt":
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    job = WindowsJob()
    process: subprocess.Popen[bytes] | None = None
    try:
        # 実体のPythonを使用し、venvラッパーの起動競合を回避する。
        process = subprocess.Popen(
            [cast(str, getattr(sys, "_base_executable")), "-c", _BOOTSTRAP, *command],
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        job.assign(process)
        try:
            stdout, stderr = process.communicate(input=b"x", timeout=timeout)
        except subprocess.TimeoutExpired as error:
            job.terminate_and_wait()
            stdout, stderr = process.communicate(timeout=5)
            raise subprocess.TimeoutExpired(
                command,
                timeout,
                output=stdout.decode("utf-8", "replace"),
                stderr=stderr.decode("utf-8", "replace"),
            ) from error
        job.terminate_and_wait()
        return subprocess.CompletedProcess(
            command,
            process.returncode,
            stdout.decode("utf-8", "replace"),
            stderr.decode("utf-8", "replace"),
        )
    finally:
        job.close()
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
