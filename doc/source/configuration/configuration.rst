.. _configuration:

AVL-JTAG Configuration
======================

AVL-JTAG is configured via the provided RTL interface and the driver's OpenOCD configuration.

RTL Interface
-------------

The default interface does not contain any modports or clocking blocks to remain compatible with \
the majority of simulators.

Connection of the interface to the DUT should be done with standard assign statements or port connections.

The optional TRSTn and SRSTn signals are enabled with the ``HAS_TRST`` and ``HAS_SRST`` parameters. \
Assertion checks for optional signals that are not included ensure they remain unchanged during simulation.

.. literalinclude:: ../../../avl_jtag/rtl/avl_jtag.sv
    :language: verilog


Integrating with a Build Environment
------------------------------------

AVL-JTAG comes with a tools utility :func:`avl_jtag._tools.get_verilog` to help integrate the library into your build environment.

This is exposed to the environment as the command line tool `avl-jtag-get-verilog` which returns a list of all RTL files required \
for AVL-JTAG.

.. code-block:: makefile

    # HDL source files
    VERILOG_SOURCES      += $(shell avl-jtag-get-verilog)

    # include cocotb's make rules to take care of the simulator setup
    include $(shell cocotb-config --makefiles)/Makefile.sim


Connecting to the AVL Environment
---------------------------------

The recommended way to connect to the AVL environment is via the factory.

.. code-block:: python

    avl.Factory.set_variable("*.hdl", dut.jtag_if)

When the agent is created it will automatically use this factory setting to connect to the JTAG interface.

OpenOCD Configuration
---------------------

The driver generates the adapter configuration (``remote_bitbang`` host / port, Tcl RPC port, gdb and telnet disabled). \
The scan chain and any targets are described with ``openocd_cfg`` - a list of OpenOCD commands executed before ``init``:

.. code-block:: python

    avl.Factory.set_variable("*.agent.drv.openocd_cfg", [
        "jtag newtap avl tap -irlen 4 -expected-id 0xdeadbeef",
        "reset_config trst_only",
    ])

Existing board / target scripts can be re-used with ``source``:

.. code-block:: python

    avl.Factory.set_variable("*.agent.drv.openocd_cfg", ["source [find target/my_target.cfg]"])

Driver Variables
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Description
   * - ``tck_period``
     - ``10``
     - TCK period
   * - ``time_unit``
     - ``"ns"``
     - Unit of ``tck_period``
   * - ``openocd``
     - ``$OPENOCD`` or ``openocd``
     - OpenOCD executable
   * - ``openocd_cfg``
     - ``["jtag newtap avl tap -irlen 4"]``
     - Commands executed before ``init``
   * - ``openocd_args``
     - ``[]``
     - Additional command line arguments (e.g. ``["-d3"]``)
   * - ``openocd_log``
     - ``<driver path>.openocd.log``
     - OpenOCD log file (None to discard)
   * - ``timeout``
     - ``30.0``
     - Wall-clock seconds without bitbang activity before failing
