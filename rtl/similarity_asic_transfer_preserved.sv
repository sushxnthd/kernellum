`timescale 1ns/1ps
`ifndef ASIC_ROWS
`define ASIC_ROWS 5
`endif
`ifndef ASIC_COLS
`define ASIC_COLS 8
`endif

module similarity_asic_transfer_preserved #(
    parameter integer ROWS = `ASIC_ROWS,
    parameter integer COLS = `ASIC_COLS,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32
) (
    input wire clk,
    input wire rst,
    output reg [31:0] digest
);
    reg [ROWS*PRECISION-1:0] a_source;
    reg [COLS*PRECISION-1:0] b_source;
    reg clear_acc;
    reg step;
    (* keep *) wire [ROWS*COLS*ACC_WIDTH-1:0] acc_flat;
    integer r, c, p;

    always @(posedge clk) begin
        if (rst) begin
            clear_acc <= 1'b1;
            step <= 1'b0;
            for (r = 0; r < ROWS; r = r + 1)
                a_source[r*PRECISION +: PRECISION] <= r + 1;
            for (c = 0; c < COLS; c = c + 1)
                b_source[c*PRECISION +: PRECISION] <= c + 3;
        end else begin
            clear_acc <= 1'b0;
            step <= 1'b1;
            for (r = 0; r < ROWS; r = r + 1)
                a_source[r*PRECISION +: PRECISION] <=
                    a_source[r*PRECISION +: PRECISION] + r + 1;
            for (c = 0; c < COLS; c = c + 1)
                b_source[c*PRECISION +: PRECISION] <=
                    b_source[c*PRECISION +: PRECISION] + (2*c) + 1;
        end
    end

    kernellum_preserved_selective_mac_array #(
        .ROWS(ROWS), .COLS(COLS), .STRIDE(2),
        .PRECISION(PRECISION), .ACC_WIDTH(ACC_WIDTH)
    ) u_array (
        .clk(clk), .rst(rst), .clear_acc(clear_acc), .step(step),
        .a_vec(a_source), .b_vec(b_source), .acc_flat(acc_flat)
    );

    always @* begin
        digest = 0;
        for (p = 0; p < ROWS*COLS; p = p + 1)
            digest = digest ^ acc_flat[p*ACC_WIDTH +: ACC_WIDTH];
    end
endmodule

