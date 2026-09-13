# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library Monitor

import avl
import cocotb
from cocotb.triggers import FallingEdge, RisingEdge

from ._item import ScanItem
from ._tap import TapState


class Monitor(avl.Monitor):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the Monitor for the JTAG agent.

        The monitor is independent of OpenOCD. It follows the TAP state machine from the pins
        and publishes a :any:`ScanItem` for every IR / DR scan (on entry to Update) and every
        entry to Test-Logic-Reset.

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

        self.i_f = avl.Factory.get_variable(f"{self.get_full_name()}.i_f", None)

        self.state = TapState.RESET
        """Current TAP state"""

        self._item = None
        self._tms_ones = 0

    def _enter_reset_(self) -> None:
        if self.state != TapState.RESET:
            item = ScanItem(f"from_{self.name}", self)
            item.scan = "RESET"
            self.item_export.write(item)
        self.state = TapState.RESET
        self._item = None

    async def _wait_on_trst_(self) -> None:
        while True:
            await FallingEdge(self.i_f.trst_n)
            self._enter_reset_()

    async def run_phase(self):
        """
        Run phase for the Monitor.

        Samples TMS / TDI / TDO on each rising edge of TCK.
        """

        if hasattr(self.i_f, "trst_n"):
            cocotb.start_soon(self._wait_on_trst_())

        while True:
            await RisingEdge(self.i_f.tck)

            if self.i_f.get("trst_n", 1) == 0:
                self._enter_reset_()
                continue

            tms = self.i_f.get("tms")

            # 5 TMS=1 clocks reach Test-Logic-Reset from any state - resynchronize
            self._tms_ones = self._tms_ones + 1 if tms else 0

            state = self.state
            if state in (TapState.DRCAPTURE, TapState.IRCAPTURE):
                self._item = ScanItem(f"from_{self.name}", self)
                self._item.scan = "DR" if state == TapState.DRCAPTURE else "IR"

            elif state in (TapState.DRSHIFT, TapState.IRSHIFT) and self._item is not None:
                self._item.tdi |= self.i_f.get("tdi") << self._item.length
                self._item.tdo |= self.i_f.get("tdo", unresolved=1) << self._item.length
                self._item.length += 1

            elif state in (TapState.DRPAUSE, TapState.IRPAUSE) and self._item is not None and tms:
                self._item.pauses += 1

            next_state = state.next(tms)

            if self._tms_ones >= 5:
                next_state = TapState.RESET

            if next_state in (TapState.DRUPDATE, TapState.IRUPDATE) and self._item is not None:
                self.item_export.write(self._item)
                self._item = None

            if next_state == TapState.RESET:
                self._enter_reset_()
            else:
                self.state = next_state

__all__ = ["Monitor"]
