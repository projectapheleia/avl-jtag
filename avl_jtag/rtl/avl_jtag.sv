// Copyright 2025 Apheleia
//
// Description:
// Apheleia Verification Library JTAG Interface
// As defined in IEEE 1149.1

`define AVL_JTAG_IMPL_CHECK(cond, signal) \
if (``cond`` == 1) begin : ``signal``_cond \
    initial begin \
        #0.1; \
        @(``signal``) $fatal("%m: ``signal`` not supported in configuration");\
    end \
end : ``signal``_cond

interface jtag_if #(parameter string CLASSIFICATION = "JTAG",
                    parameter bit    HAS_TRST       = 1,
                    parameter bit    HAS_SRST       = 0)();

    logic tck;      // Test clock                   (driven by OpenOCD)
    logic tms;      // Test mode select             (driven by OpenOCD)
    logic tdi;      // Test data in                 (driven by OpenOCD)
    logic tdo;      // Test data out                (driven by DUT)
    logic trst_n;   // Optional test reset          (driven by OpenOCD)
    logic srst_n;   // Optional system reset        (driven by OpenOCD)

    generate

        `AVL_JTAG_IMPL_CHECK((HAS_TRST == 0), trst_n)

        `AVL_JTAG_IMPL_CHECK((HAS_SRST == 0), srst_n)

    endgenerate

endinterface : jtag_if

`undef AVL_JTAG_IMPL_CHECK
