# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library Agent

import avl
from cocotb.handle import HierarchyObject
from cocotb.triggers import NextTimeStep, Timer

from ._agent_cfg import AgentCfg
from ._bandwidth import Bandwidth
from ._coverage import Coverage
from ._driver import Driver
from ._interface import Interface
from ._monitor import Monitor
from ._sequence import Sequence


class Agent(avl.Agent):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the avl-jtag Agent

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

        # Create configuration and export to children
        self.cfg = avl.Factory.get_variable(f"{self.get_full_name()}.cfg", AgentCfg("cfg", self))
        avl.Factory.set_variable(f"{self.get_full_name()}.*.cfg", self.cfg)

        # Bind HDL to establish parameters and configuration
        self._bind_(avl.Factory.get_variable(f"{self.get_full_name()}.hdl", None))

        # Create sequencer and driver if enabled
        if self.cfg.has_driver:
            self.sqr = avl.Sequencer("sqr", self)
            self.seq = Sequence("seq", self.sqr)
            self.drv = Driver("drv", self)
            self.sqr.seq_item_export.connect(self.drv.seq_item_port)

        # Create monitor if enabled
        if self.cfg.has_monitor:
            self.monitor = Monitor("monitor", self)

            if self.cfg.has_coverage:
                self.coverage = Coverage("coverage", self)
                self.monitor.item_export.connect(self.coverage.item_port)

            if self.cfg.has_bandwidth:
                self.bandwidth = Bandwidth("bandwidth", self)
                self.monitor.item_export.connect(self.bandwidth.item_port)

            if self.cfg.has_trace:
                self.trace = avl.Trace("trace", self)
                self.monitor.item_export.connect(self.trace.item_port)

    def _bind_(self, hdl) -> None:
        """
        Bind the agent to a hardware description language (HDL) interface.
        This method is used to associate the agent with a specific HDL interface,
        allowing it to interact with the hardware model.

        :param hdl: The HDL interface to bind to the agent
        :type hdl: HierarchyObject
        :raises TypeError: If `hdl` is not an instance of HierarchyObject
        """
        if not isinstance(hdl, HierarchyObject):
            raise TypeError(f"Expected HierarchyObject, got {type(hdl)}")

        # Assign Interface
        self.i_f = Interface(hdl)
        avl.Factory.set_variable(f"{self.get_full_name()}.*.i_f", self.i_f)

    async def run_phase(self) -> None:
        """
        Run the agent's phase. This method is called to start the agent's operation.
        It starts the sequence (if the driver is enabled) and shuts OpenOCD down once complete.
        """

        self.raise_objection()
        await NextTimeStep()

        if self.cfg.has_driver:
            try:
                await self.seq.start()
            except BaseException:
                # Sequence failed or test cancelled - never leave OpenOCD running
                self.drv.ocd.stop()
                raise
            await self.drv.shutdown()

            # Run-off
            await Timer(10 * self.drv.tck_period, unit=self.drv.time_unit)

        self.drop_objection()

__all__ = ["Agent"]
