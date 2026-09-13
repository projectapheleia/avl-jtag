// Copyright 2025 Apheleia
//
// Description:
// Minimal IEEE 1149.1 TAP used by the AVL-JTAG examples
//
// Instructions (IR_WIDTH = 4):
//   0x1 IDCODE  - 32-bit identification register (selected after reset)
//   0x8 USER    - 32-bit read / write scratch register
//   0xF BYPASS  - 1-bit bypass register (also used for all other codes)

module example_tap #(parameter logic [31:0] IDCODE = 32'hDEADBEEF)
(
    input  logic        tck,
    input  logic        tms,
    input  logic        tdi,
    input  logic        trst_n,
    output logic        tdo,
    output logic [31:0] user_reg
);

    localparam logic [3:0] IR_IDCODE = 4'h1;
    localparam logic [3:0] IR_USER   = 4'h8;
    localparam logic [3:0] IR_BYPASS = 4'hF;

    typedef enum logic [3:0] {
        TLR, RTI,
        SEL_DR, CAP_DR, SH_DR, EX1_DR, PAU_DR, EX2_DR, UPD_DR,
        SEL_IR, CAP_IR, SH_IR, EX1_IR, PAU_IR, EX2_IR, UPD_IR
    } state_t;

    state_t      state, next_state;
    logic [3:0]  ir, ir_sr;
    logic [31:0] dr_sr;
    logic        bypass_sr;

    // TAP state machine
    always_comb begin
        case (state)
            TLR    : next_state = tms ? TLR    : RTI;
            RTI    : next_state = tms ? SEL_DR : RTI;
            SEL_DR : next_state = tms ? SEL_IR : CAP_DR;
            CAP_DR : next_state = tms ? EX1_DR : SH_DR;
            SH_DR  : next_state = tms ? EX1_DR : SH_DR;
            EX1_DR : next_state = tms ? UPD_DR : PAU_DR;
            PAU_DR : next_state = tms ? EX2_DR : PAU_DR;
            EX2_DR : next_state = tms ? UPD_DR : SH_DR;
            UPD_DR : next_state = tms ? SEL_DR : RTI;
            SEL_IR : next_state = tms ? TLR    : CAP_IR;
            CAP_IR : next_state = tms ? EX1_IR : SH_IR;
            SH_IR  : next_state = tms ? EX1_IR : SH_IR;
            EX1_IR : next_state = tms ? UPD_IR : PAU_IR;
            PAU_IR : next_state = tms ? EX2_IR : PAU_IR;
            EX2_IR : next_state = tms ? UPD_IR : SH_IR;
            UPD_IR : next_state = tms ? SEL_DR : RTI;
            default: next_state = TLR;
        endcase
    end

    always_ff @(posedge tck or negedge trst_n) begin
        if (!trst_n) state <= TLR;
        else         state <= next_state;
    end

    // Instruction register
    always_ff @(posedge tck or negedge trst_n) begin
        if (!trst_n) begin
            ir    <= IR_IDCODE;
            ir_sr <= '0;
        end else begin
            case (state)
                TLR    : ir    <= IR_IDCODE;
                CAP_IR : ir_sr <= 4'b0101;
                SH_IR  : ir_sr <= {tdi, ir_sr[3:1]};
                UPD_IR : ir    <= ir_sr;
                default: ;
            endcase
        end
    end

    // Data registers
    always_ff @(posedge tck or negedge trst_n) begin
        if (!trst_n) begin
            dr_sr     <= '0;
            bypass_sr <= 1'b0;
            user_reg  <= '0;
        end else begin
            case (state)
                CAP_DR : begin
                    bypass_sr <= 1'b0;
                    case (ir)
                        IR_IDCODE: dr_sr <= IDCODE;
                        IR_USER  : dr_sr <= user_reg;
                        default  : dr_sr <= '0;
                    endcase
                end
                SH_DR  : begin
                    dr_sr     <= {tdi, dr_sr[31:1]};
                    bypass_sr <= tdi;
                end
                UPD_DR : if (ir == IR_USER) user_reg <= dr_sr;
                default: ;
            endcase
        end
    end

    // TDO changes on the falling edge of TCK
    always_ff @(negedge tck) begin
        case (state)
            SH_IR  : tdo <= ir_sr[0];
            SH_DR  : tdo <= (ir == IR_IDCODE || ir == IR_USER) ? dr_sr[0] : bypass_sr;
            default: tdo <= 1'b0;
        endcase
    end

endmodule : example_tap
