`timescale 1ns/1ps

`ifndef ASIC_ROWS
`define ASIC_ROWS 2
`endif

`ifndef ASIC_COLS
`define ASIC_COLS 4
`endif

module similarity_asic_transport_core #(
    parameter integer ROWS = `ASIC_ROWS,
    parameter integer COLS = `ASIC_COLS,
    parameter integer TRANSPORT = 0,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire        clk,
    input  wire        rst,
    output reg  [31:0] digest
);
    reg [ROWS*PRECISION-1:0] a_source;
    reg [COLS*PRECISION-1:0] b_source;
    reg                       clear_acc;
    reg                       step;

    (* keep *) wire [ROWS*COLS*ACC_WIDTH-1:0] acc_flat;

    integer r;
    integer c;
    integer p;

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

    always @* begin
        digest = 32'b0;
        for (p = 0; p < ROWS*COLS; p = p + 1)
            digest = digest ^ acc_flat[p*ACC_WIDTH +: ACC_WIDTH];
    end

    generate
        if (TRANSPORT == 0) begin : g_broadcast
            kernellum_mac_array #(
                .ROWS(ROWS),
                .COLS(COLS),
                .PRECISION(PRECISION),
                .ACC_WIDTH(ACC_WIDTH),
                .BUFFER_KB(1),
                .DATAFLOW(1)
            ) u_array (
                .clk(clk),
                .rst(rst),
                .clear_acc(clear_acc),
                .step(step),
                .a_vec(a_source),
                .b_vec(b_source),
                .acc_flat(acc_flat),
                .scratch_we(1'b0),
                .scratch_addr(8'b0),
                .scratch_wdata(32'b0),
                .scratch_rdata()
            );
        end else begin : g_local
            kernellum_local_mac_array #(
                .ROWS(ROWS),
                .COLS(COLS),
                .PRECISION(PRECISION),
                .ACC_WIDTH(ACC_WIDTH)
            ) u_array (
                .clk(clk),
                .rst(rst),
                .clear_acc(clear_acc),
                .step(step),
                .a_vec(a_source),
                .b_vec(b_source),
                .acc_flat(acc_flat)
            );
        end
    endgenerate
endmodule

module similarity_asic_transfer_broadcast #(
    parameter integer ROWS = `ASIC_ROWS,
    parameter integer COLS = `ASIC_COLS
) (
    input  wire        clk,
    input  wire        rst,
    output wire [31:0] digest
);
    similarity_asic_transport_core #(
        .ROWS(ROWS),
        .COLS(COLS),
        .TRANSPORT(0)
    ) u_core (
        .clk(clk),
        .rst(rst),
        .digest(digest)
    );
endmodule

module similarity_asic_transfer_local #(
    parameter integer ROWS = `ASIC_ROWS,
    parameter integer COLS = `ASIC_COLS
) (
    input  wire        clk,
    input  wire        rst,
    output wire [31:0] digest
);
    similarity_asic_transport_core #(
        .ROWS(ROWS),
        .COLS(COLS),
        .TRANSPORT(1)
    ) u_core (
        .clk(clk),
        .rst(rst),
        .digest(digest)
    );
endmodule
