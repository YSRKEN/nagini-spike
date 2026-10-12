"""Windows の Job オブジェクトで、起動したプロセスを子孫ごと止める。"""

import ctypes
import subprocess
import time
from typing import Any


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
    """Job のネイティブハンドルを所有する。閉じると所属するプロセスもすべて終わる。"""

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
