#!/bin/bash

# Environment setup
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export AVL_JTAG_ROOT="$SCRIPT_DIR"

# Graphviz setup
if ! command -v dot &> /dev/null
then
    echo "WARNING : Graphviz could not be found. Please install Graphviz and ensure it is in your PATH (see https://graphviz.org/download/) if you want to generate docs and run all examples."
fi

# OpenOCD setup
export OPENOCD=${OPENOCD:-openocd}
if ! command -v $OPENOCD &> /dev/null
then
    echo "WARNING : OpenOCD could not be found. Please install OpenOCD (see https://openocd.org/pages/getting-openocd.html) or set OPENOCD to the executable path. The JTAG driver requires it."
elif ! $OPENOCD -c "adapter list" -c shutdown 2>&1 | grep -q remote_bitbang
then
    echo "WARNING : $OPENOCD was not built with the remote_bitbang adapter driver. The JTAG driver requires it."
fi

# Python setup

pushd $AVL_JTAG_ROOT 1>/dev/null

python_packages=(\
".[dev]"
)

python3 -m venv venv
source ./venv/bin/activate
for p in ${python_packages[@]}; do
    python3 -m pip install --editable $p
done

popd 1>/dev/null

# Default Simulation setup
export CXXFLAGS=${CXXFLAGS:--std=c++17}
export PYTHONPATH=${PYTHONPATH}
export SIM=${SIM:-verilator}
export TOPLEVEL_LANG=${TOPLEVEL_LANG:-verilog}
