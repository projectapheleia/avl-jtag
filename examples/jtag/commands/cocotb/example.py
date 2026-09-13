# Copyright 2024 Apheleia
#
# Description:
# Apheleia JTAG commands example - raw OpenOCD commands supplied via the factory


import avl
import avl_jtag
import cocotb


class example_env(avl.Env):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.agent = avl_jtag.Agent("agent", self)

    async def run_phase(self):
        self.raise_objection()
        cocotb.start_soon(self.timeout(100, units="ms"))
        self.drop_objection()

@cocotb.test
async def test(dut):
    avl.Factory.set_variable("*.hdl", dut.jtag_if)
    avl.Factory.set_variable("*.agent.cfg.has_driver", True)
    avl.Factory.set_variable("*.agent.cfg.has_monitor", True)
    avl.Factory.set_variable("*.agent.cfg.has_trace", True)

    avl.Factory.set_variable("*.agent.drv.openocd_cfg", [
        "jtag newtap avl tap -irlen 4 -expected-id 0xdeadbeef",
        "reset_config trst_only",
    ])

    # Any OpenOCD Tcl - executed in order by the default sequence body
    avl.Factory.set_variable("*.agent.sqr.seq.commands", [
        "scan_chain",
        "adapter assert trst",
        "adapter deassert trst",
        "runtest 5",
        "irscan avl.tap 0x1",
        "drscan avl.tap 32 0",
        "irscan avl.tap 0x8",
        "drscan avl.tap 16 0xbeef 16 0xdead",
        "drscan avl.tap 32 0",
        "proc user_rw {v} { irscan avl.tap 0x8; drscan avl.tap 32 $v }",
        "user_rw 0x01234567",
        "user_rw 0x89abcdef",
    ])

    e = example_env("env", None)
    await e.start()

    # Monitor observed the user register value written by the last command
    assert int(dut.user_reg.value) == 0x89ABCDEF
