# AVL-JTAG - Apheleia Verification Library JTAG Verification Component

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)


AVL-JTAG provides a simple, extensible verification component for [IEEE 1149.1 JTAG](https://standards.ieee.org/ieee/1149.1/4484/) \
developed in [Python](https://www.python.org/) and the [AVL](https://avl-core.readthedocs.io/en/latest/index.html) library.

Unlike a conventional bus VIP, the driver does not implement the protocol itself. Instead it uses \
[OpenOCD](https://openocd.org/pages/about.html) with the `remote_bitbang` adapter:

```
 Sequence ──(OpenOCD Tcl command)──► Driver ──Tcl RPC──► OpenOCD
                                       ▲                    │
                                       └── remote_bitbang ◄─┘
                                       │
                            TCK/TMS/TDI/TRST ► DUT ► TDO
```

- Sequences issue any OpenOCD Tcl command (`irscan`, `drscan`, `runtest`, `pathmove`, `jtag_reset`, `scan_chain`, user procs, targets...)
- The driver is the remote_bitbang server - each bitbang request becomes pin activity on the interface
- Simulation time only advances on bitbang requests, so runs are deterministic regardless of host load
- The monitor is independent of OpenOCD and reconstructs IR / DR scans from the pins

AVL is built on the [CocoTB](https://docs.cocotb.org/en/stable/) framework, but aims to combine the best elements of \
[UVM](https://accellera.org/community/uvm) in a more engineer friendly and efficient way.

## Protocol Features

| Signal Name | Description | Driven By |
|-------------|-------------|-----------|
| TCK         | Test clock. | OpenOCD |
| TMS         | Test mode select - sampled on the rising edge of TCK to move the TAP state machine. | OpenOCD |
| TDI         | Test data in - sampled on the rising edge of TCK in Shift-IR / Shift-DR. | OpenOCD |
| TDO         | Test data out - changes on the falling edge of TCK. | DUT |
| TRSTn       | Optional asynchronous active-low TAP reset. | OpenOCD |
| SRSTn       | Optional active-low system reset. | OpenOCD |

## Component Features

- OpenOCD driven sequence / sequencer / driver
- Convenience sequence API: `command`, `irscan`, `drscan`, `runtest`, `pathmove`
- Simple RTL interface to interact with HDL and define configuration options
- TAP state machine monitor generating IR, DR and reset items
- Bandwidth monitor generating bit activity plots over user defined windows during simulation
- Functional coverage
- Searchable trace file generation

---

## 📦 Installation

OpenOCD must be installed and built with the `remote_bitbang` adapter (`openocd -c "adapter list"`). \
Set `OPENOCD` to use a specific executable.

### Using `pip`
```sh
# Standard build
pip install avl-jtag

# Development build
pip install avl-jtag[dev]
```

### Install from Source
```sh
git clone https://github.com/projectapheleia/avl-jtag.git
cd avl-jtag

# Standard build
pip install .

# Development build
pip install .[dev]
```

Alternatively if you want to create a [virtual environment](https://docs.python.org/3/library/venv.html) rather than install globally a script is provided. This will install, with edit privileges to local virtual environment.

This script assumes you have [Graphviz](https://graphviz.org/download/), [OpenOCD](https://openocd.org/) and appropriate simulator installed, so all examples and documentation will build out of the box.


```sh
git clone https://github.com/projectapheleia/avl-jtag.git
cd avl-jtag
source avl-jtag.sh
```

## 🚀 Usage

```python
class MySequence(avl_jtag.Sequence):
    async def body(self):
        await self.irscan(0x1)
        idcode = await self.drscan(32, 0)
        item = await self.command("scan_chain")
        self.info(item.response)

avl.Factory.set_variable("*.hdl", dut.jtag_if)
avl.Factory.set_variable("*.agent.cfg.has_driver", True)
avl.Factory.set_variable("*.agent.cfg.has_monitor", True)
avl.Factory.set_variable("*.agent.drv.openocd_cfg", ["jtag newtap avl tap -irlen 4", "reset_config trst_only"])
avl.Factory.set_override_by_type(avl_jtag.Sequence, MySequence)
```

## 📖 Documentation

In order to build the documentation you must have installed the development build.

### Build from Source
```sh
cd doc
make html
<browser> build/html/index.html
```
## 🏃 Examples

In order to run all the examples you must have installed the development build.

To run all examples:

```sh
cd examples

# To run
make -j 8 sim

# To clean
make -j 8 clean
```

To run an individual example:

```sh
cd examples/THE EXAMPLE YOU WANT

# To run
make sim

# To clean
make clean
```

The examples use the [CocoTB Makefile](https://docs.cocotb.org/en/stable/building.html) and default to [Verilator](https://www.veripool.org/verilator/) with waveforms generated (`dump.vcd`) - use `make sim WAVES=0` to disable. This can be modified using the standard CocoTB build system.

Rendered waveforms for each example are included in the documentation (regenerate with `python3 doc/gen_waveforms.py` after running the examples).

---


## 🧹 Code Style & Linting

This project uses [**Ruff**](https://docs.astral.sh/ruff/) for linting and formatting.

Check code for issues:

```sh
ruff check .
```

Automatically fix common issues:

```sh
ruff check . --fix
```



## 📧 Contact

- Email: avl@projectapheleia.net
- GitHub: [projectapheleia](https://github.com/projectapheleia)
