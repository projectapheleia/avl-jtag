# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library Interface

from typing import Any

from cocotb.handle import HierarchyObject

parameters = [
    "CLASSIFICATION",
    "HAS_TRST",
    "HAS_SRST",
]

signals = [
  "tck",
  "tms",
  "tdi",
  "tdo",
  "trst_n",
  "srst_n",
]

class Interface:
    def __init__(self, hdl : HierarchyObject) -> None:
        """
        Create an interface
        Work around simulator specific issues with accessing signals inside generates.
        """
        # Parameters
        for p in parameters:
            # Parameters not exposed by list() in some simulators - look up explicitly
            v = getattr(hdl, p)
            if isinstance(v.value, bytes):
                setattr(self, p, str(v.value.decode("utf-8")))
            else:
                setattr(self, p, int(v.value))

        # Signals
        for s in signals:
            # Some simulators do not expose signals inside interfaces through list(hdl).
            # Populate the _sub_handle cache explicitly.
            child = getattr(hdl, s)
            setattr(self, child._name, child)

        if self.CLASSIFICATION != "JTAG":
            raise TypeError(f"Expected JTAG classification, got {self.CLASSIFICATION}")

        # Remove un-configured signals
        if self.HAS_TRST == 0:
            delattr(self, "trst_n")

        if self.HAS_SRST == 0:
            delattr(self, "srst_n")

    def set(self, name : str, value : int) -> None:
        """
        Set the value of a signal (if signal exists)

        :param name: The name of the signal
        :type name: str
        :param value: The value to set
        :type value: int
        :return: None
        """
        signal = getattr(self, name, None)
        if signal is not None:
            signal.value = value

    def get(self, name : str, default : Any = None, unresolved : int = 0) -> int:
        """
        Get the value of a signal (if signal exists)

        :param name: The name of the signal
        :type name: str
        :param default: The default value to return if signal does not exist
        :type default: Any
        :param unresolved: Value substituted for X / Z bits (e.g. 1 to model a pull-up on TDO)
        :type unresolved: int
        :return: The value of the signal or the default value
        :rtype: int
        """
        signal = getattr(self, name, None)
        if signal is not None:
            try:
                return int(signal.value)
            except ValueError:
                bits = "".join(c if c in "01" else str(unresolved) for c in str(signal.value))
                return int(bits, 2)
        return default

__all__ = ["Interface"]
