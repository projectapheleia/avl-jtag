# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library Tools

from importlib.resources import files


def get_verilog():
    """
    Get the path to the Verilog source files for the JTAG agent.

    :return: Path to the Verilog source files
    :rtype: pathlib.Path
    """
    path = files("avl_jtag.rtl").joinpath("avl_jtag.sv")
    print(path)
