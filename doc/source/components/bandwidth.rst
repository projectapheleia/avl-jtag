.. _bandwidth:

AVL-JTAG Bandwidth
==================

.. inheritance-diagram:: avl_jtag._bandwidth
    :parts: 1

The :doc:`avl_jtag.Bandwidth </modules/avl_jtag._bandwidth>` component counts the number of bits shifted in each \
``window_ns`` time window and generates a plot during the report phase.

.. code-block:: python

    avl.Factory.set_variable("*.agent.cfg.has_bandwidth", True)
    avl.Factory.set_variable("*.agent.bandwidth.window_ns", 1000)
