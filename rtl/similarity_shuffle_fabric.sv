`timescale 1ns/1ps

module similarity_shuffle_fabric #(
    parameter integer N = 7,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire clk,
    input  wire rst,
    output wire [31:0] digest
);
    reg [7:0] counter;
    (* keep *) reg signed [PRECISION-1:0] a_edge [0:N-1];
    (* keep *) reg signed [PRECISION-1:0] b_edge [0:N-1];

    integer i;
    always @(posedge clk) begin
        if (rst) begin
            counter <= 0;
            for (i=0;i<N;i=i+1) begin
                a_edge[i] <= i + 1;
                b_edge[i] <= i + 2;
            end
        end else begin
            counter <= counter + 1'b1;
            for (i=0;i<N;i=i+1) begin
                a_edge[i] <= $signed(counter) + i + 1;
                b_edge[i] <= $signed(counter) - i - 1;
            end
        end
    end

    wire [N*N*ACC_WIDTH-1:0] acc_flat;

    genvar r,c;
    generate
        for (r=0;r<N;r=r+1) begin : g_row
            for (c=0;c<N;c=c+1) begin : g_col
                (* keep *) reg signed [PRECISION-1:0] a_local;
                (* keep *) reg signed [PRECISION-1:0] b_local;
                wire signed [2*PRECISION-1:0] product;
                wire signed [ACC_WIDTH-1:0] product_ext;
                (* keep *) reg signed [ACC_WIDTH-1:0] accumulator;

                localparam integer A_PREV_ROW = (r + c) % N;
                localparam integer B_PREV_COL = (c + 2*r) % N;

                assign product = a_local * b_local;
                assign product_ext =
                    {{(ACC_WIDTH-2*PRECISION){product[2*PRECISION-1]}}, product};

                always @(posedge clk) begin
                    if (rst) begin
                        a_local <= 0;
                        b_local <= 0;
                        accumulator <= 0;
                    end else begin
                        if (c == 0)
                            a_local <= a_edge[r];
                        else
                            a_local <= g_row[A_PREV_ROW].g_col[c-1].a_local;

                        if (r == 0)
                            b_local <= b_edge[c];
                        else
                            b_local <= g_row[r-1].g_col[B_PREV_COL].b_local;

                        accumulator <= accumulator + product_ext;
                    end
                end

                assign acc_flat[(r*N+c)*ACC_WIDTH +: ACC_WIDTH] = accumulator;
            end
        end
    endgenerate

    assign digest =
        acc_flat[0 +: 32] ^
        acc_flat[(N*N-1)*ACC_WIDTH +: 32];
endmodule
