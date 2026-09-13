# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library Sequence Items

import avl


class SequenceItem(avl.SequenceItem):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the sequence item.

        A sequence item carries a single OpenOCD Tcl command to the driver, which
        executes it over the OpenOCD Tcl RPC port and returns the result.

        :param name: Name of the sequence item
        :param parent: Parent component of the sequence item
        """
        super().__init__(name, parent)

        self.cmd = ""
        """OpenOCD Tcl command (e.g. ``irscan avl.tap 0x1``)"""

        self.rc = 0
        """Tcl return code (0 = TCL_OK, 1 = TCL_ERROR, ...)"""

        self.response = ""
        """Tcl result string returned by OpenOCD"""

        self.set_field_attributes("rc", compare=False)
        self.set_field_attributes("response", compare=False)

        # By default transpose to make more readable
        self.set_table_fmt(transpose=True)


class ScanItem(avl.SequenceItem):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the scan item.

        Scan items are produced by the monitor from the observed JTAG pins. One item is
        generated for each completed IR or DR scan and each entry into Test-Logic-Reset.

        :param name: Name of the scan item
        :param parent: Parent component of the scan item
        """
        super().__init__(name, parent)

        self.scan = "DR"
        """Scan type: ``IR``, ``DR`` or ``RESET``"""

        self.length = 0
        """Number of bits shifted"""

        self.tdi = 0
        """Bits shifted in on TDI (LSB first)"""

        self.tdo = 0
        """Bits shifted out on TDO (LSB first)"""

        self.pauses = 0
        """Number of times the scan passed through the Pause state"""

        self.set_field_attributes("pauses", compare=False)

        # By default transpose to make more readable
        self.set_table_fmt(transpose=True)

__all__ = ["SequenceItem", "ScanItem"]
