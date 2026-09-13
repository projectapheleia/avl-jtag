.. _protocol:

Protocol
========

JTAG
----

.. list-table::
   :header-rows: 1

   * - Signal
     - Description
     - Driven By
   * - TCK
     - Test clock.
     - OpenOCD
   * - TMS
     - Test mode select - sampled on the rising edge of TCK.
     - OpenOCD
   * - TDI
     - Test data in - sampled on the rising edge of TCK in Shift-IR / Shift-DR.
     - OpenOCD
   * - TDO
     - Test data out - changes on the falling edge of TCK.
     - DUT
   * - TRSTn
     - Optional asynchronous active-low TAP reset.
     - OpenOCD
   * - SRSTn
     - Optional active-low system reset.
     - OpenOCD

The TAP controller is a 16 state machine clocked by TCK and steered by TMS:

.. graphviz::

   digraph tap {
      rankdir=TB;
      node [shape=box, style=rounded, fontsize=10];
      edge [fontsize=9];
      RESET -> RESET [label="1"]; RESET -> IDLE [label="0"];
      IDLE -> IDLE [label="0"]; IDLE -> DRSELECT [label="1"];
      DRSELECT -> DRCAPTURE [label="0"]; DRSELECT -> IRSELECT [label="1"];
      DRCAPTURE -> DRSHIFT [label="0"]; DRCAPTURE -> DREXIT1 [label="1"];
      DRSHIFT -> DRSHIFT [label="0"]; DRSHIFT -> DREXIT1 [label="1"];
      DREXIT1 -> DRPAUSE [label="0"]; DREXIT1 -> DRUPDATE [label="1"];
      DRPAUSE -> DRPAUSE [label="0"]; DRPAUSE -> DREXIT2 [label="1"];
      DREXIT2 -> DRSHIFT [label="0"]; DREXIT2 -> DRUPDATE [label="1"];
      DRUPDATE -> IDLE [label="0"]; DRUPDATE -> DRSELECT [label="1"];
      IRSELECT -> IRCAPTURE [label="0"]; IRSELECT -> RESET [label="1"];
      IRCAPTURE -> IRSHIFT [label="0"]; IRCAPTURE -> IREXIT1 [label="1"];
      IRSHIFT -> IRSHIFT [label="0"]; IRSHIFT -> IREXIT1 [label="1"];
      IREXIT1 -> IRPAUSE [label="0"]; IREXIT1 -> IRUPDATE [label="1"];
      IRPAUSE -> IRPAUSE [label="0"]; IRPAUSE -> IREXIT2 [label="1"];
      IREXIT2 -> IRSHIFT [label="0"]; IREXIT2 -> IRUPDATE [label="1"];
      IRUPDATE -> IDLE [label="0"]; IRUPDATE -> DRSELECT [label="1"];
   }

OpenOCD remote_bitbang
----------------------

OpenOCD's ``remote_bitbang`` adapter sends single ASCII character requests over a socket. \
The AVL-JTAG driver is the socket server and converts each request into pin activity:

.. list-table::
   :header-rows: 1

   * - Request
     - Meaning
     - Simulation action
   * - ``0`` - ``7``
     - Write TCK (bit 2), TMS (bit 1), TDI (bit 0)
     - Drive pins, wait TCK/2
   * - ``R``
     - Read TDO
     - Reply ``0`` / ``1``
   * - ``r`` - ``u``
     - Reset: bit 1 TRST asserted, bit 0 SRST asserted
     - Drive TRSTn / SRSTn, wait TCK/2
   * - ``B`` ``b``
     - Blink LED on / off
     - Ignored
   * - ``Q``
     - Quit
     - Ignored

Commands are sent to OpenOCD over its Tcl RPC port (messages terminated by ``0x1a``). \
Each command is wrapped with ``catch`` so the Tcl return code and result are both returned to the sequence item.

.. note::

    Simulation time only advances in response to bitbang write and reset requests. \
    While OpenOCD is processing, the simulator waits in wall-clock time. \
    Simulation results are therefore deterministic and independent of host load.
