# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library OpenOCD process and socket management

import atexit
import ctypes
import os
import select
import signal
import socket
import subprocess
import sys
import weakref

TCL_TERMINATOR = b"\x1a"

# Live instances - stopped at interpreter exit as a last resort
_instances: "weakref.WeakSet[OpenOcd]" = weakref.WeakSet()


@atexit.register
def _stop_all() -> None:
    for ocd in list(_instances):
        ocd.stop(timeout=1.0)


def _exit_with_parent(parent_pid: int):
    """
    Return a pre-exec hook that makes the kernel kill OpenOCD if the simulator process dies
    (crash, $fatal, SIGKILL) before Python has a chance to clean up. Linux only.

    :param parent_pid: PID of the launching (simulator) process
    """
    def hook() -> None:
        try:
            PR_SET_PDEATHSIG = 1
            ctypes.CDLL(None, use_errno=True).prctl(PR_SET_PDEATHSIG, signal.SIGKILL)
        except Exception:
            pass
        # Parent already gone before the death signal was armed
        if os.getppid() != parent_pid:
            os._exit(1)
    return hook


def _free_port(host: str) -> int:
    """
    Ask the OS for a free TCP port.

    :param host: Host address to bind
    :return: Port number
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


class OpenOcd:
    def __init__(self, executable: str, config: list[str], host: str = "127.0.0.1", logfile: str | None = None, args: list[str] | None = None) -> None:
        """
        OpenOCD process connected to the simulation via the remote_bitbang adapter.

        The simulation acts as the remote_bitbang *server*; OpenOCD connects to it as a client
        and sends ASCII bitbang requests. Commands are sent to OpenOCD over its Tcl RPC port.

        All socket operations are non-simulation-time aware - the owner is responsible for
        servicing the bitbang stream (see :class:`avl_jtag._driver.Driver`).

        :param executable: OpenOCD executable
        :param config: OpenOCD configuration commands executed before ``init``
        :param host: Loopback address used for both sockets
        :param logfile: OpenOCD log file (None = discard)
        :param args: Additional OpenOCD command line arguments
        """
        self.executable = executable
        self.config = config
        self.host = host
        self.logfile = logfile
        self.args = args or []

        self.proc: subprocess.Popen | None = None
        self.listener: socket.socket | None = None
        self.bitbang: socket.socket | None = None
        self.tcl: socket.socket | None = None
        self.tcl_port = 0
        self.tcl_buf = bytearray()
        self._log = None

    def start(self) -> None:
        """
        Open the remote_bitbang listening socket and launch OpenOCD.
        """
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((self.host, 0))
        self.listener.listen(1)
        bitbang_port = self.listener.getsockname()[1]
        self.tcl_port = _free_port(self.host)

        commands = [
            "adapter driver remote_bitbang",
            f"remote_bitbang host {self.host}",
            f"remote_bitbang port {bitbang_port}",
            f"bindto {self.host}",
            "gdb_port disabled",
            "telnet_port disabled",
            f"tcl_port {self.tcl_port}",
            *self.config,
            "init",
        ]

        cmdline = [self.executable, *self.args]
        for c in commands:
            cmdline += ["-c", c]

        if self.logfile is not None:
            self._log = open(self.logfile, "w")
        self.proc = subprocess.Popen(cmdline, stdin=subprocess.DEVNULL,
                                     stdout=self._log if self._log else subprocess.DEVNULL,
                                     stderr=subprocess.STDOUT,
                                     preexec_fn=_exit_with_parent(os.getpid()) if sys.platform.startswith("linux") else None)
        _instances.add(self)

    def check_alive(self) -> None:
        """
        Raise if the OpenOCD process has exited.
        """
        if self.proc is not None and self.proc.poll() is not None:
            where = f" - see {os.path.abspath(self.logfile)}" if self.logfile else ""
            raise RuntimeError(f"OpenOCD exited unexpectedly with code {self.proc.returncode}{where}")

    def try_connect_tcl(self) -> bool:
        """
        Attempt to connect to the OpenOCD Tcl RPC port.

        :return: True if connected
        """
        if self.tcl is not None:
            return True
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.host, self.tcl_port))
        except OSError:
            s.close()
            return False
        s.setblocking(False)
        self.tcl = s
        return True

    def wait(self, timeout: float) -> tuple[bool, bool]:
        """
        Block (wall-clock) until OpenOCD has bitbang or Tcl data available.

        Accepts the remote_bitbang connection when it arrives.

        :param timeout: Maximum time to wait in seconds
        :return: Tuple of (bitbang readable, tcl readable)
        """
        rlist = [s for s in (self.listener if self.bitbang is None else None, self.bitbang, self.tcl) if s is not None]
        readable, _, _ = select.select(rlist, [], [], timeout)

        if self.listener in readable and self.bitbang is None:
            self.bitbang, _ = self.listener.accept()
            self.bitbang.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.bitbang.setblocking(False)

        return (self.bitbang is not None and self.bitbang in readable,
                self.tcl is not None and self.tcl in readable)

    def recv_bitbang(self) -> bytes | None:
        """
        Read all available bitbang requests.

        :return: Request bytes, None if nothing is available, empty if the connection was closed
        """
        try:
            data = self.bitbang.recv(65536)
        except BlockingIOError:
            return None
        if not data:
            self.bitbang.close()
            self.bitbang = None
        return data

    def send_bitbang(self, data: bytes) -> None:
        """
        Send bitbang responses (TDO samples) back to OpenOCD.

        :param data: Response bytes
        """
        if self.bitbang is not None and data:
            self.bitbang.setblocking(True)
            try:
                self.bitbang.sendall(data)
            finally:
                self.bitbang.setblocking(False)

    def send_tcl(self, cmd: str) -> None:
        """
        Send a Tcl command to OpenOCD. The command is wrapped so both the return code and result are returned.

        :param cmd: Tcl command
        """
        self.tcl_buf.clear()
        wrapped = f"set _avl_rc [catch {{{cmd}}} _avl_res]; format \"%d %s\" $_avl_rc $_avl_res"
        self.tcl.setblocking(True)
        try:
            self.tcl.sendall(wrapped.encode() + TCL_TERMINATOR)
        finally:
            self.tcl.setblocking(False)

    def recv_tcl(self) -> tuple[int, str] | None:
        """
        Collect Tcl response data.

        :return: (return code, result) once the full response has been received, otherwise None
        """
        try:
            data = self.tcl.recv(65536)
        except BlockingIOError:
            data = None
        if data == b"":
            raise RuntimeError("OpenOCD closed the Tcl RPC connection")
        if data:
            self.tcl_buf += data

        if TCL_TERMINATOR not in self.tcl_buf:
            return None

        response = bytes(self.tcl_buf[:self.tcl_buf.index(TCL_TERMINATOR)]).decode(errors="replace")
        self.tcl_buf.clear()
        rc, _, result = response.partition(" ")
        try:
            return int(rc), result
        except ValueError:
            return 1, response

    def stop(self, timeout: float = 1.0) -> None:
        """
        Close sockets and terminate OpenOCD. Safe to call multiple times.

        :param timeout: Time to wait after SIGTERM before killing the process
        """
        for s in (self.tcl, self.bitbang, self.listener):
            if s is not None:
                s.close()
        self.tcl = self.bitbang = self.listener = None

        if self.proc is not None:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait()
            self.proc = None
            _instances.discard(self)

        if self._log is not None:
            self._log.close()
            self._log = None

__all__ = ["OpenOcd"]
