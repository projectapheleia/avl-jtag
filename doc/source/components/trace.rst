.. _trace:

AVL-JTAG Trace
==============

The trace uses the standard `avl.Trace <https://avl-core.readthedocs.io/en/latest/>`_ component to write every \
monitored scan item to a CSV file (``env.agent.trace.csv`` by default).

.. code-block:: python

    avl.Factory.set_variable("*.agent.cfg.has_trace", True)
