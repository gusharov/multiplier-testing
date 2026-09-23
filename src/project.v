/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_example (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    // Configure bidirectional pins as inputs
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Control signals mapped to bidirectional pins
    wire load_a    = uio_in[0];
    wire load_b    = uio_in[1];
    wire latch_res = uio_in[2];
    wire [1:0] out_sel = uio_in[4:3];

    // Registers to bound the combinational logic for accurate STA timing
    reg [15:0] reg_a;
    reg [15:0] reg_b;
    reg [31:0] reg_p;

    wire [31:0] mul_out;

    // Shift registers to load 16-bit operands via 8-bit input pins
    always @(posedge clk) begin
        if (!rst_n) begin
            reg_a <= 16'b0;
            reg_b <= 16'b0;
            reg_p <= 32'b0;
        end else begin
            if (load_a) reg_a <= {reg_a[7:0], ui_in};
            if (load_b) reg_b <= {reg_b[7:0], ui_in};
            if (latch_res) reg_p <= mul_out;
        end
    end

    // 16x16 Array Multiplier Combinational Logic
    wire [31:0] partials [0:15];
    wire [31:0] sums [0:15];
    
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : pp_gen
            assign partials[i] = reg_b[i] ? ({16'b0, reg_a} << i) : 32'b0;
        end
    endgenerate

    assign sums[0] = partials[0];
    generate
        for (i = 1; i < 16; i = i + 1) begin : adder_chain
            assign sums[i] = sums[i-1] + partials[i];
        end
    endgenerate

    assign mul_out = sums[15];

    // Multiplex the 32-bit result out through the 8-bit output pins
    assign uo_out = (out_sel == 2'b00) ? reg_p[7:0]   :
                    (out_sel == 2'b01) ? reg_p[15:8]  :
                    (out_sel == 2'b10) ? reg_p[23:16] :
                                         reg_p[31:24] ;

    // Tie off unused inputs
    wire _unused = &{ena, uio_in[7:5]};

endmodule
