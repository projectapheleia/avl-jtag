.. _waveforms:

Waveforms
=========

The waveforms below are taken from the examples. Every OpenOCD bitbang write lasts half a TCK period \
(``tck_period`` = 10 ns), so the pin activity is exactly what OpenOCD generated for each command.

The ``state``, ``ir``, ``ir_sr``, ``dr_sr`` and ``user_reg`` rows are internal to the example TAP (``examples/rtl/example_tap.sv``).

Running an example with Verilator writes ``dump.vcd`` to the example directory.

To regenerate these images after running the examples:

.. code-block:: bash

    python3 doc/gen_waveforms.py

Directed Example
----------------

OpenOCD init
~~~~~~~~~~~~
The end of OpenOCD's scan chain examination (a long DR scan of 1s through the chain), a TMS reset, \
then the IR length probe.

.. image:: /images/jtag_init.png

IDCODE
~~~~~~
The IDCODE instruction is loaded (``ir_sr`` captures ``0x5``, the mandatory ``01`` pattern) and \
``0xdeadbeef`` is shifted out on TDO, LSB first.

.. image:: /images/jtag_idcode.png

USER Register Write
~~~~~~~~~~~~~~~~~~~
``0xcafebabe`` is shifted in on TDI and loaded into ``user_reg`` on Update-DR.

.. image:: /images/jtag_user.png

Pause and pathmove
~~~~~~~~~~~~~~~~~~
A DR scan ending in Pause-DR, followed by an explicit ``pathmove`` back to Run-Test/Idle via Exit2-DR and Update-DR.

.. image:: /images/jtag_pause.png

Bypass
~~~~~~
With BYPASS selected, ``0xa5`` appears on TDO delayed by one bit.

.. image:: /images/jtag_bypass.png

Commands Example
----------------

TRST
~~~~
``adapter assert trst`` / ``adapter deassert trst`` pulse TRSTn, which resets the TAP asynchronously, followed by \
``runtest`` and an ``irscan``.

.. image:: /images/jtag_trst.png

Tcl Procedure
~~~~~~~~~~~~~
A user defined Tcl ``proc`` issuing an ``irscan`` and ``drscan`` as a single sequence item.

.. image:: /images/jtag_user_proc.png
