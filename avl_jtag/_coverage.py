# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library Coverage

import avl

from ._item import ScanItem


class Coverage(avl.Component):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize Coverage

        Class contains variable ir_width. When set (via the factory) instruction values are covered.

        :param name: Name of the coverage class.
        :type name: str
        :param parent: Parent component.
        :type parent: Component
        """
        super().__init__(name, parent)

        self.ir_width = avl.Factory.get_variable(f"{self.get_full_name()}.ir_width", None)
        """Instruction register width - enables instruction coverage (default None)"""

        self.item_port = avl.List()
        self.item = ScanItem("for_coverage", self)

        # Define coverage
        self.cg = avl.Covergroup("jtag", self)
        self.cg.set_comment("JTAG Coverage")

        # Scan type
        self.cp_scan = self.cg.add_coverpoint("scan", lambda: self.item.scan)
        self.cp_scan.set_comment("Scan type")
        for s in ["IR", "DR", "RESET"]:
            self.cp_scan.add_bin(s, lambda x, y=s : x == y)

        # IR length
        self.cp_ir_length = self.cg.add_coverpoint("ir_length", lambda: self.item.length if self.item.scan == "IR" else -1)
        self.cp_ir_length.set_comment("IR scan length (bits)")
        self.cp_ir_length.add_bin("bits", range(1, 1024), stats=True)

        # DR length
        self.cp_dr_length = self.cg.add_coverpoint("dr_length", lambda: self.item.length if self.item.scan == "DR" else -1)
        self.cp_dr_length.set_comment("DR scan length (bits)")
        self.cp_dr_length.add_bin("1", 1)
        self.cp_dr_length.add_bin("2-31", range(2, 32))
        self.cp_dr_length.add_bin("32", 32)
        self.cp_dr_length.add_bin(">32", range(33, 1 << 16))
        self.cp_dr_length.add_bin("bits", range(1, 1 << 16), stats=True)

        # Pause
        self.cp_pause = self.cg.add_coverpoint("pause", lambda: self.item.pauses if self.item.scan != "RESET" else -1)
        self.cp_pause.set_comment("Scan used Pause state")
        self.cp_pause.add_bin("no", 0)
        self.cp_pause.add_bin("yes", range(1, 1 << 16))

        self.cc_scanXpause = self.cg.add_covercross("scanXpause", self.cp_scan, self.cp_pause)
        self.cc_scanXpause.set_comment("Cross scan type and Pause")

        if self.ir_width is not None:
            # Instruction
            self.cp_instruction = self.cg.add_coverpoint("instruction",
                                                         lambda: self.item.tdi if self.item.scan == "IR" and self.item.length == self.ir_width else -1)
            self.cp_instruction.set_comment("Instruction loaded")
            for i in range(1 << self.ir_width):
                self.cp_instruction.add_bin(f"{i:#x}", i)

        # TDI / TDO bits (first 32)
        self.cp_tdi = self.cg.add_coverpoint("tdi", lambda: self.item.tdi)
        self.cp_tdi.set_comment("TDI bits")
        self.cp_tdo = self.cg.add_coverpoint("tdo", lambda: self.item.tdo)
        self.cp_tdo.set_comment("TDO bits")
        for i in range(32):
            self.cp_tdi.add_bin(f"[{i}] == 0", lambda x, y=i : 0 == (x & (1<<y)))
            self.cp_tdi.add_bin(f"[{i}] == 1", lambda x, y=i : 0 != (x & (1<<y)))
            self.cp_tdo.add_bin(f"[{i}] == 0", lambda x, y=i : 0 == (x & (1<<y)))
            self.cp_tdo.add_bin(f"[{i}] == 1", lambda x, y=i : 0 != (x & (1<<y)))

    async def run_phase(self) -> None:
        """
        Run phase for the coverage component.

        """

        while True:
            # Wait for an item to be available
            self.item = await self.item_port.blocking_get()

            # Sample
            self.cg.sample()

__all__ = ["Coverage"]
