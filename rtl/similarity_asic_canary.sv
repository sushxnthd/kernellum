`timescale 1ns/1ps

module similarity_asic_broadcast_canary (
    input  wire        clk,
    input  wire        rst,
    output wire [31:0] digest
);
    similarity_broadcast_fabric #(
        .ROWS(3),
        .COLS(3),
        .PRECISION(8),
        .ACC_WIDTH(32)
    ) u_fabric (
        .clk(clk),
        .rst(rst),
        .digest(digest)
    );
endmodule

module similarity_asic_local_canary (
    input  wire        clk,
    input  wire        rst,
    output wire [31:0] digest
);
    similarity_local_fabric #(
        .ROWS(3),
        .COLS(3),
        .PRECISION(8),
        .ACC_WIDTH(32)
    ) u_fabric (
        .clk(clk),
        .rst(rst),
        .digest(digest)
    );
endmodule
