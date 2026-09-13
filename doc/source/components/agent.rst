.. _agent:

AVL-JTAG Agent
==============

.. inheritance-diagram:: avl_jtag._agent_cfg
    :parts: 1

.. inheritance-diagram:: avl_jtag._agent
    :parts: 1

Unlike many VIPs AVL-JTAG does not contain an environment.

The AVL-JTAG verification component is designed to be integrated easily into existing AVL environments, and \
as such an agent can be individually configured without a wider global environment.

To configure the agent, the user must override the :doc:`avl_jtag.AgentCfg </modules/avl_jtag._agent_cfg>` class. \
The best way to do this is via the factory:

.. code-block:: python

    avl.Factory.set_variable("*.agent.cfg.has_driver", True)
    avl.Factory.set_variable("*.agent.cfg.has_monitor", True)
    avl.Factory.set_variable("*.agent.cfg.has_coverage", True)

When the driver is enabled the agent runs its sequence to completion, then shuts OpenOCD down.

Sub-Components
--------------

.. toctree::
   :maxdepth: 1

   sequence
   driver
   monitor
   bandwidth
   coverage
   trace
