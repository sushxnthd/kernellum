`timescale 1ns/1ps

module kernellum_mac_array #(
    parameter integer ROWS = 8,
    parameter integer COLS = 8,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32,
    parameter integer BUFFER_KB = 64,
    parameter integer DATAFLOW = 0,
    parameter integer SCRATCH_WORDS = (BUFFER_KB * 1024) / 4,
    parameter integer SCRATCH_ADDR_W = (SCRATCH_WORDS <= 1) ? 1 : $clog2(SCRATCH_WORDS)
) (
    input  wire                               clk,
    input  wire                               rst,
    input  wire                               clear_acc,
    input  wire                               step,
    input  wire [ROWS*PRECISION-1:0]          a_vec,
    input  wire [COLS*PRECISION-1:0]          b_vec,
    output wire [ROWS*COLS*ACC_WIDTH-1:0]     acc_flat,

    input  wire                               scratch_we,
    input  wire [SCRATCH_ADDR_W-1:0]          scratch_addr,
    input  wire [31:0]                        scratch_wdata,
    output reg  [31:0]                        scratch_rdata
);
    // DATAFLOW is intentionally retained as an architectural parameter for K1.
    // K0.5 validates the shared MAC-array and scratchpad resource model first.
    wire _unused_dataflow = DATAFLOW[0];

    (* ram_style = "block" *) reg [31:0] scratch [0:SCRATCH_WORDS-1];

    always @(posedge clk) begin
        if (scratch_we)
            scratch[scratch_addr] <= scratch_wdata;
        scratch_rdata <= scratch[scratch_addr];
    end

    genvar r, c;
    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_row
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                wire signed [PRECISION-1:0] a_lane;
                wire signed [PRECISION-1:0] b_lane;
                wire signed [2*PRECISION-1:0] product;
                wire signed [ACC_WIDTH-1:0] product_ext;
                reg  signed [ACC_WIDTH-1:0] accumulator;

                assign a_lane = a_vec[r*PRECISION +: PRECISION];
                assign b_lane = b_vec[c*PRECISION +: PRECISION];
                assign product = a_lane * b_lane;
                assign product_ext = {{(ACC_WIDTH-2*PRECISION){product[2*PRECISION-1]}}, product};

                always @(posedge clk) begin
                    if (rst || clear_acc)
                        accumulator <= {ACC_WIDTH{1'b0}};
                    else if (step)
                        accumulator <= accumulator + product_ext;
                end

                assign acc_flat[(r*COLS+c)*ACC_WIDTH +: ACC_WIDTH] = accumulator;
            end
        end
    endgenerate
endmodule
