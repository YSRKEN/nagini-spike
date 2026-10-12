"""Nagini の ``--server`` を起動したまま保ち、題材の検証を1件ずつ頼む。

サーバは要求を1つずつ順に処理するので、クライアント側で待つのをやめても検証は止まらない。
時間切れのときは、サーバをその子孫（Z3）ごと止めて起動し直す。
"""

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Literal

import zmq

if sys.platform == "win32":
    from scripts.process_runner import WindowsJob

SERVER_URL = "tcp://127.0.0.1:5555"
READY = "Server started successfully"
STARTUP_TIMEOUT = 120.0

# Job への所属を済ませるまで、サーバ本体を起動させない。
_BOOTSTRAP = (
    "import subprocess,sys; "
    "sys.stdin.buffer.read(1); "
    "sys.exit(subprocess.call(sys.argv[1:], stdin=subprocess.DEVNULL))"
)


@dataclass(frozen=True)
class Reply:
    """サーバへの1回の要求の結果。

    Attributes
    ----------
    status : {"answered", "timeout", "crashed"}
        応答が返った、時間切れになった、サーバが途中で終わった、のどれか。
    text : str
        応答の本文。サーバが終わったときは、その間にサーバが出した出力。
    seconds : float
        要求から結果が分かるまでの秒数。
    """

    status: Literal["answered", "timeout", "crashed"]
    text: str
    seconds: float


class NaginiServer:
    """起動したままの Nagini サーバ1つを所有する。

    Parameters
    ----------
    root : Path
        サーバの作業ディレクトリ。
    placeholder : Path
        ``--server`` の起動に要る題材ファイル。サーバモードでは検証されない。
    """

    def __init__(self, root: Path, placeholder: Path) -> None:
        self.root = root
        self.placeholder = placeholder
        self.context: zmq.Context[zmq.Socket[bytes]] = zmq.Context.instance()
        self.process: subprocess.Popen[bytes] | None = None
        self.job: WindowsJob | None = None
        self.output: list[str] = []

    def __enter__(self) -> "NaginiServer":
        """サーバを起動して返す。"""
        self.start()
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        """サーバを止める。"""
        self.stop()

    def start(self) -> None:
        """サーバを起動し、要求を受け付けるまで待つ。

        Raises
        ------
        RuntimeError
            決めた時間内に受け付けを始めなかった、または途中で終了した。
        """
        command = [sys.executable, "-m", "nagini_translation.main", "--server"]
        command.append(str(self.placeholder))
        environment = os.environ.copy()
        environment["PYTHONUTF8"] = "1"
        # 仮想環境の外の Python から起動すると、Nagini が Z3 を見つけられない。
        z3 = Path(sys.prefix) / "bin" / ("z3.exe" if sys.platform == "win32" else "z3")
        if not z3.is_file():
            raise FileNotFoundError(f"仮想環境に同梱された Z3 が無い: {z3}")
        environment["Z3_EXE"] = str(z3)
        if sys.platform == "win32":
            self.job = WindowsJob()
            base = str(getattr(sys, "_base_executable"))
            self.process = subprocess.Popen(
                [base, "-c", _BOOTSTRAP, *command],
                cwd=self.root,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.job.assign(self.process)
            assert self.process.stdin is not None
            self.process.stdin.write(b"x")
            self.process.stdin.close()
        else:
            self.process = subprocess.Popen(
                command,
                cwd=self.root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        self._wait_ready()

    def _wait_ready(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        stdout = self.process.stdout
        ready = threading.Event()
        output: list[str] = []
        self.output = output

        def read() -> None:
            for raw in stdout:
                line = raw.decode("utf-8", "replace")
                output.append(line)
                if READY in line:
                    ready.set()

        threading.Thread(target=read, daemon=True).start()
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while not ready.wait(0.1):
            if self.process.poll() is not None or time.monotonic() > deadline:
                self.stop()
                raise RuntimeError("Nagini サーバが起動しない:\n" + "".join(output))

    def stop(self) -> None:
        """サーバを子孫ごと止める。"""
        if self.process is None:
            return
        if sys.platform == "win32":
            if self.job is not None:
                self.job.terminate_and_wait()
                self.job.close()
                self.job = None
        elif self.process.poll() is None:
            os.killpg(self.process.pid, 9)
        self.process.wait(timeout=10)
        self.process = None

    def verify(self, path: Path, select: str | None, timeout: float) -> Reply:
        """題材を1件検証する。

        Parameters
        ----------
        path : Path
            題材ファイルの絶対パス。
        select : str or None
            検証する関数・クラスの名前（カンマ区切り）。None ならファイル全体。
        timeout : float
            待つ秒数。過ぎたらサーバを起動し直す。

        Returns
        -------
        Reply
            Nagini の応答。時間切れやサーバの異常終了のときは、サーバを起動し直してから返す。
        """
        assert self.process is not None
        request: dict[str, str] = {"file": str(path)}
        if select:
            request["select"] = select
        socket = self.context.socket(zmq.REQ)
        socket.setsockopt(zmq.LINGER, 0)
        socket.connect(SERVER_URL)
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        mark = len(self.output)
        start = time.perf_counter()
        socket.send_string(json.dumps(request))
        reply: Reply | None = None
        try:
            while reply is None:
                seconds = time.perf_counter() - start
                if poller.poll(200):
                    reply = Reply("answered", socket.recv_string(), seconds)
                elif self.process.poll() is not None:
                    # Nagini は変換中の Python 例外を捕まえず、サーバごと終わる。
                    reply = Reply("crashed", "".join(self.output[mark:]), seconds)
                elif seconds > timeout:
                    reply = Reply("timeout", "", seconds)
        finally:
            socket.close()
        if reply.status != "answered":
            self.stop()
            self.start()
        return reply
