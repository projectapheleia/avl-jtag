# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library OpenOCD remote_bitbang Driver

import os
import time
from collections.abc import Callable

import avl
from cocotb.triggers import Timer

from ._item import SequenceItem
from ._openocd import OpenOcd


class Driver(avl.Driver):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the OpenOCD Driver for the JTAG agent.

        Rather than driving the pins itself, the driver launches OpenOCD with the remote_bitbang
        adapter and acts as the bitbang server. Each sequence item is an OpenOCD Tcl command which is
        sent to OpenOCD over its Tcl RPC port; the resulting bitbang requests are converted to pin
        activity on the JTAG interface.

        Simulation time only advances in response to bitbang requests. While OpenOCD is busy the
        simulator is blocked (wall-clock), so results are independent of host load.

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

        self.i_f = avl.Factory.get_variable(f"{self.get_full_name()}.i_f", None)

        self.tck_period = avl.Factory.get_variable(f"{self.get_full_name()}.tck_period", 10)
        """TCK period (in time_unit). Each bitbang write request lasts half a period."""

        self.time_unit = avl.Factory.get_variable(f"{self.get_full_name()}.time_unit", "ns")
        """Time unit for tck_period"""

        self.openocd = avl.Factory.get_variable(f"{self.get_full_name()}.openocd", os.environ.get("OPENOCD", "openocd"))
        """OpenOCD executable (default $OPENOCD or openocd)"""

        self.openocd_cfg = avl.Factory.get_variable(f"{self.get_full_name()}.openocd_cfg", ["jtag newtap avl tap -irlen 4"])
        """
        OpenOCD configuration commands, executed after the adapter setup and before ``init``.
        Typically ``jtag newtap`` / ``reset_config`` / target definitions.
        """

        self.openocd_args = avl.Factory.get_variable(f"{self.get_full_name()}.openocd_args", [])
        """Additional OpenOCD command line arguments (e.g. ``["-d3"]``)"""

        self.openocd_log = avl.Factory.get_variable(f"{self.get_full_name()}.openocd_log", f"{self.get_full_name()}.openocd.log")
        """OpenOCD log file (None to discard)"""

        self.timeout = avl.Factory.get_variable(f"{self.get_full_name()}.timeout", 30.0)
        """Wall-clock timeout (seconds) waiting on OpenOCD with no bitbang activity"""

        self.ocd = OpenOcd(self.openocd, self.openocd_cfg, logfile=self.openocd_log, args=self.openocd_args)
        self._unknown: set[int] = set()

    async def reset(self) -> None:
        """
        Reset the driver by setting all signals to their default values.

        TCK low, TMS high (so any clocking moves the TAP toward Test-Logic-Reset), TDI low and resets de-asserted.
        """

        self.i_f.set("tck", 0)
        self.i_f.set("tms", 1)
        self.i_f.set("tdi", 0)
        self.i_f.set("trst_n", 1)
        self.i_f.set("srst_n", 1)

    async def _half_period(self) -> None:
        await Timer(self.tck_period / 2, unit=self.time_unit)

    async def _bitbang_(self, data: bytes) -> None:
        """
        Execute a block of remote_bitbang requests on the interface.

        Protocol (see OpenOCD doc/manual/jtag/drivers/remote_bitbang.txt):

        - ``0``-``7`` : write TCK/TMS/TDI (bit 2 / 1 / 0)
        - ``R``       : read TDO, respond ``0`` or ``1``
        - ``r``-``u`` : reset - bit 1 TRST asserted, bit 0 SRST asserted
        - ``B`` / ``b``: blink LED on / off (ignored)
        - ``Q``       : quit

        :param data: Request bytes
        """
        reply = bytearray()
        for c in data:
            if 0x30 <= c <= 0x37:
                v = c - 0x30
                self.i_f.set("tms", (v >> 1) & 1)
                self.i_f.set("tdi", v & 1)
                self.i_f.set("tck", (v >> 2) & 1)
                await self._half_period()
            elif c == 0x52:  # R
                # Model a pull-up on an undriven TDO
                reply.append(0x31 if self.i_f.get("tdo", 1, unresolved=1) else 0x30)
            elif 0x72 <= c <= 0x75:  # r s t u
                v = c - 0x72
                self.i_f.set("trst_n", 0 if (v >> 1) & 1 else 1)
                self.i_f.set("srst_n", 0 if v & 1 else 1)
                await self._half_period()
            elif c in (0x42, 0x62, 0x0A, 0x0D):  # B b \n \r
                pass
            elif c == 0x51:  # Q
                self.debug("OpenOCD sent quit")
            elif c not in self._unknown:
                self._unknown.add(c)
                self.warning(f"Ignoring unsupported remote_bitbang request {chr(c)!r}")

        self.ocd.send_bitbang(bytes(reply))

    async def _service_(self, done: Callable[[], bool]) -> None:
        """
        Service OpenOCD bitbang requests until done() returns True.

        :param done: Completion predicate evaluated after each event
        """
        deadline = time.monotonic() + self.timeout
        while not done():
            self.ocd.check_alive()

            bitbang, _ = self.ocd.wait(0.01)
            if bitbang:
                data = self.ocd.recv_bitbang()
                if data:
                    await self._bitbang_(data)
                    deadline = time.monotonic() + self.timeout

            if time.monotonic() > deadline:
                raise TimeoutError(f"No response from OpenOCD for {self.timeout}s - see {self.openocd_log}")

    async def start_openocd(self) -> None:
        """
        Launch OpenOCD and service the scan chain initialization until the Tcl RPC port is available.
        """
        self.info(f"Starting OpenOCD ({self.openocd})")
        self.ocd.start()
        await self._service_(self.ocd.try_connect_tcl)

        # Round-trip a no-op to ensure init has fully completed
        self.ocd.send_tcl("version")
        await self._service_(lambda: self._poll_tcl_())
        self.info(f"OpenOCD ready: {self._result[1]}")

    def _poll_tcl_(self) -> bool:
        self._result = self.ocd.recv_tcl()
        return self._result is not None

    async def shutdown(self) -> None:
        """
        Shut OpenOCD down gracefully.
        """
        try:
            if self.ocd.tcl is not None and self.ocd.proc is not None:
                self.ocd.send_tcl("shutdown")
                await self._service_(lambda: self.ocd.bitbang is None or self.ocd.proc.poll() is not None)
        except (OSError, RuntimeError, TimeoutError):
            pass
        finally:
            self.ocd.stop()

    async def drive(self, item : SequenceItem) -> None:
        """
        Execute the OpenOCD command in the sequence item and capture the result.

        :param item: The sequence item containing the command to execute
        :type item: SequenceItem
        """
        self.debug(f"OpenOCD> {item.cmd}")
        self.ocd.send_tcl(item.cmd)
        await self._service_(self._poll_tcl_)
        item.rc, item.response = self._result
        self.debug(f"OpenOCD< [{item.rc}] {item.response}")

    async def run_phase(self):
        """
        Run phase for the Driver.

        Pulses TRST (if present), launches OpenOCD and then executes sequence items in order.
        """
        await self.reset()

        # Reset TAP
        self.i_f.set("trst_n", 0)
        await Timer(self.tck_period, unit=self.time_unit)
        self.i_f.set("trst_n", 1)
        await Timer(self.tck_period, unit=self.time_unit)

        try:
            await self.start_openocd()

            while True:
                item = await self.seq_item_port.blocking_get()
                await self.drive(item)
                item.set_event("done")
        except BaseException:
            self.ocd.stop()
            raise

    async def report_phase(self) -> None:
        """
        Ensure OpenOCD has been terminated.
        """
        self.ocd.stop()

__all__ = ["Driver"]
