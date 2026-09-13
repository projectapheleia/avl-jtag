.. _coverage:

AVL-JTAG Coverage
=================

.. inheritance-diagram:: avl_jtag._coverage
    :parts: 1

The :doc:`avl_jtag.Coverage </modules/avl_jtag._coverage>` component samples each monitored scan item:

- Scan type (IR, DR, RESET)
- IR and DR scan lengths (with statistics)
- Use of the Pause states, crossed with scan type
- TDI / TDO bits 0-31
- Instruction values (when ``ir_width`` is set)

.. code-block:: python

    avl.Factory.set_variable("*.agent.cfg.has_coverage", True)
    avl.Factory.set_variable("*.agent.coverage.ir_width", 4)
