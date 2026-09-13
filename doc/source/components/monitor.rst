.. _monitor:

AVL-JTAG Monitor
================

.. inheritance-diagram:: avl_jtag._monitor
    :parts: 1

The :doc:`avl_jtag.Monitor </modules/avl_jtag._monitor>` is independent of OpenOCD. It follows the TAP state machine \
by sampling TMS on each rising edge of TCK and publishes a :doc:`avl_jtag.ScanItem </modules/avl_jtag._item>`:

- On entry to Update-IR / Update-DR - ``scan`` is ``IR`` or ``DR`` with ``length``, ``tdi``, ``tdo`` (LSB first) and ``pauses``
- On entry to Test-Logic-Reset (TMS or TRSTn) - ``scan`` is ``RESET``

The monitor starts in Test-Logic-Reset and re-synchronizes after 5 consecutive TCK cycles with TMS high.
