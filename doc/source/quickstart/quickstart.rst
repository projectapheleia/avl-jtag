Quickstart Guide
================

This guide will help you get started with the AVL JTAG library. It will show you how to install the library, compile and run the examples, \
and how to use the library in your own projects.

Before you start this guide, you should have a basic understanding of `AVL <https://avl-core.readthedocs.io/en/latest/>`_.

In order to run the examples you will need to have installed:

- `Python <https://www.python.org/downloads/>`_

- `OpenOCD <https://openocd.org/pages/getting-openocd.html>`_ built with the ``remote_bitbang`` adapter
    - Check with ``openocd -c "adapter list" -c shutdown``
    - Set the ``OPENOCD`` environment variable to use a specific executable

- A HDL simulator
    - If you haven't licensed a commercial HDL simulator `Verilator <https://www.veripool.org/wiki/verilator>`_ is available as an open-source alternative.

It's also recommended that you have a basic understanding of the `cocotb <https://docs.cocotb.org/en/stable/>`_ framework.

Installing From pip
---------------------

.. code-block:: bash

    # Standard build
    pip install avl-jtag

    # Development build
    pip install avl-jtag[dev]

Installing From Source
----------------------

.. code-block:: bash

    git clone https://github.com/projectapheleia/avl-jtag.git
    cd avl-jtag

    # Standard build
    pip install .

    # Development build
    pip install .[dev]

A script is provided to setup a python virtual environment and install all dependencies for development.

.. code-block:: bash

    git clone https://github.com/projectapheleia/avl-jtag.git
    cd avl-jtag
    source avl-jtag.sh

This assumes you have a simulator, OpenOCD and `Graphviz <https://graphviz.gitlab.io/download/>`_ installed, to ensure all examples and documentation can be built out of the box.

Building The Docs
-----------------

.. code-block:: bash

    cd doc
    make html
    <browser> build/html/index.html

Running the Examples
--------------------

The examples are located in the examples directory. To run the examples, you will need to have a HDL simulator installed, the default is `Verilator <https://www.veripool.org/wiki/verilator>`_.

To run all examples:

.. code-block:: bash

    cd examples
    make sim

To clean up the examples:

.. code-block:: bash

    cd examples
    make clean

Alternatively, you can run each example individually:

.. code-block:: bash

    cd examples/jtag/directed
    make sim

Each example writes the OpenOCD log to ``env.agent.drv.openocd.log``.

If using Verilator all examples generate `vcd <https://en.wikipedia.org/wiki/Value_change_dump>`_ files (disable with ``make sim WAVES=0``). See :ref:`waveforms`.
