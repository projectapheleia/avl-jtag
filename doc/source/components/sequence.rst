.. _sequence:

AVL-JTAG Sequence
=================

.. inheritance-diagram:: avl_jtag._sequence
    :parts: 1

The :doc:`avl_jtag.Sequence </modules/avl_jtag._sequence>` issues OpenOCD Tcl commands. Each command is carried to the \
driver in a :doc:`avl_jtag.SequenceItem </modules/avl_jtag._item>` which returns the Tcl return code (``rc``) and result (``response``).

By default the body executes each command in the ``commands`` factory variable:

.. code-block:: python

    avl.Factory.set_variable("*.agent.sqr.seq.commands", [
        "irscan avl.tap 0x1",
        "drscan avl.tap 32 0",
    ])

For directed tests extend the sequence and use the helper methods:

.. list-table::
   :header-rows: 1

   * - Method
     - Description
   * - ``command(cmd, check=None)``
     - Execute any Tcl. Raises on error unless ``check=False``
   * - ``irscan(instruction, tap, endstate)``
     - Load an instruction
   * - ``drscan(length, value, tap, endstate)``
     - Shift a data register, returns the captured value
   * - ``runtest(cycles)``
     - Clock TCK in Run-Test/Idle
   * - ``pathmove(*states)``
     - Walk an explicit TAP state path

.. code-block:: python

    class DirectedSequence(avl_jtag.Sequence):
        async def body(self):
            await self.irscan(0x1)
            assert await self.drscan(32, 0) == 0xDEADBEEF

    avl.Factory.set_override_by_type(avl_jtag.Sequence, DirectedSequence)

The ``tap`` factory variable (default ``avl.tap``) sets the TAP used by the helpers.
