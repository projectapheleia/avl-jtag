# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library OpenOCD Command Sequence

import avl

from ._item import SequenceItem


class Sequence(avl.Sequence):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the sequence.

        The default body executes each OpenOCD command in ``commands`` in turn.
        Users typically extend the sequence and override ``body`` using :any:`command` or the
        :any:`irscan`, :any:`drscan`, :any:`runtest`, :any:`pathmove` helpers.

        :param name: Name of the sequence
        :param parent: Parent component of the sequence
        """
        super().__init__(name, parent)

        self.i_f = avl.Factory.get_variable(f"{self.get_full_name()}.i_f", None)
        """Handle to interface - defines capabilities and parameters"""

        self.commands = avl.Factory.get_variable(f"{self.get_full_name()}.commands", [])
        """List of OpenOCD commands executed by the default body"""

        self.tap = avl.Factory.get_variable(f"{self.get_full_name()}.tap", "avl.tap")
        """Default TAP name used by the scan helpers"""

        self.check = avl.Factory.get_variable(f"{self.get_full_name()}.check", True)
        """Raise an error if a command returns a non-zero Tcl return code"""

    async def command(self, cmd : str, check : bool | None = None) -> SequenceItem:
        """
        Execute an OpenOCD Tcl command.

        :param cmd: The command (any valid OpenOCD Tcl)
        :param check: Raise on Tcl error (default: self.check)
        :return: The completed item (``rc`` and ``response`` populated)
        """
        item = SequenceItem(f"from_{self.name}", self)
        item.cmd = cmd

        await self.start_item(item)
        await self.finish_item(item)

        if (self.check if check is None else check) and item.rc != 0:
            raise RuntimeError(f"OpenOCD command '{cmd}' failed: {item.response}")

        return item

    async def irscan(self, instruction : int, tap : str | None = None, endstate : str | None = None) -> SequenceItem:
        """
        Load an instruction into the TAP instruction register.

        :param instruction: Instruction value
        :param tap: TAP name (default self.tap)
        :param endstate: Optional end state (e.g. ``IRPAUSE``)
        :return: The completed item
        """
        cmd = f"irscan {tap or self.tap} {instruction:#x}"
        if endstate is not None:
            cmd += f" -endstate {endstate}"
        return await self.command(cmd)

    async def drscan(self, length : int, value : int, tap : str | None = None, endstate : str | None = None) -> int:
        """
        Shift a value through the currently selected data register.

        :param length: Number of bits
        :param value: Value shifted in (LSB first)
        :param tap: TAP name (default self.tap)
        :param endstate: Optional end state (e.g. ``DRPAUSE``)
        :return: Value captured from TDO
        """
        cmd = f"drscan {tap or self.tap} {length} {value:#x}"
        if endstate is not None:
            cmd += f" -endstate {endstate}"
        item = await self.command(cmd)
        return int(item.response.split()[0], 16)

    async def runtest(self, cycles : int) -> SequenceItem:
        """
        Move to Run-Test/Idle and clock TCK.

        :param cycles: Number of TCK cycles
        :return: The completed item
        """
        return await self.command(f"runtest {cycles}")

    async def pathmove(self, *states : str) -> SequenceItem:
        """
        Move the TAP through an explicit sequence of states.

        :param states: Start state followed by each subsequent state (OpenOCD state names)
        :return: The completed item
        """
        return await self.command(f"pathmove {' '.join(states)}")

    async def body(self) -> None:
        """
        Body of the sequence - execute each command in ``commands``.
        """

        self.info(f"Starting sequence {self.get_full_name()} with {len(self.commands)} commands")
        for cmd in self.commands:
            item = await self.command(cmd)
            self.info(f"{cmd} -> {item.response}")

__all__ = ["Sequence"]
