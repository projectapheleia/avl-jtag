# Copyright 2024 Apheleia
#
# Description:
# Apheleia JTAG directed example - OpenOCD commands issued from a sequence


import avl
import avl_jtag
import cocotb

IDCODE = 0xDEADBEEF
IR_IDCODE = 0x1
IR_USER = 0x8
IR_BYPASS = 0xF


class DirectedSequence(avl_jtag.Sequence):
    async def body(self) -> None:
        self.info(f"Starting directed sequence {self.get_full_name()}")

        # Scan chain discovered by OpenOCD during init
        item = await self.command("jtag names")
        assert item.response.strip() == "avl.tap", item.response

        # IDCODE
        await self.irscan(IR_IDCODE)
        idcode = await self.drscan(32, 0)
        self.info(f"IDCODE = {idcode:#010x}")
        assert idcode == IDCODE

        # User register write and read back
        await self.irscan(IR_USER)
        await self.drscan(32, 0xCAFEBABE)
        assert await self.drscan(32, 0x12345678) == 0xCAFEBABE
        assert await self.drscan(32, 0) == 0x12345678

        # Scan ending in pause, resumed with pathmove
        await self.drscan(32, 0xA5A5A5A5, endstate="DRPAUSE")
        await self.pathmove("DRPAUSE", "DREXIT2", "DRUPDATE", "IDLE")
        assert await self.drscan(32, 0) == 0xA5A5A5A5

        # Bypass - data delayed by one bit
        await self.irscan(IR_BYPASS)
        assert await self.drscan(8, 0xA5) == ((0xA5 << 1) & 0xFF)

        # Idle clocks
        await self.runtest(16)

        # Any Tcl - errors are reported back rather than failing the simulation when check=False
        item = await self.command("not_a_command", check=False)
        assert item.rc != 0
        self.info(f"Expected error: {item.response}")

        item = await self.command("expr {6 * 7}")
        assert item.response == "42"


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
    avl.Factory.set_variable("*.agent.cfg.has_coverage", True)
    avl.Factory.set_variable("*.agent.cfg.has_bandwidth", True)
    avl.Factory.set_variable("*.agent.cfg.has_trace", True)
    avl.Factory.set_variable("*.agent.coverage.ir_width", 4)
    avl.Factory.set_variable("*.agent.bandwidth.window_ns", 1000)

    # OpenOCD target description
    avl.Factory.set_variable("*.agent.drv.tck_period", 10)
    avl.Factory.set_variable("*.agent.drv.openocd_cfg", [
        f"jtag newtap avl tap -irlen 4 -expected-id {IDCODE:#x}",
        "reset_config trst_only",
    ])

    avl.Factory.set_override_by_type(avl_jtag.Sequence, DirectedSequence)
    e = example_env("env", None)
    await e.start()
