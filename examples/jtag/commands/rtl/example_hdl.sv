module example_hdl();

    jtag_if#(.HAS_TRST(1),
             .HAS_SRST(0)) jtag_if();

    logic [31:0] user_reg;

    example_tap #(.IDCODE(32'hDEADBEEF)) tap (
        .tck      (jtag_if.tck),
        .tms      (jtag_if.tms),
        .tdi      (jtag_if.tdi),
        .trst_n   (jtag_if.trst_n),
        .tdo      (jtag_if.tdo),
        .user_reg (user_reg)
    );

endmodule : example_hdl
