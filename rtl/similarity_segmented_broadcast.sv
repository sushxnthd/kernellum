`timescale 1ns/1ps

module similarity_segmented_broadcast #(
    parameter integer N = 8,
    parameter integer A_FANOUT = 8,
    parameter integer B_FANOUT = 8,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire clk,
    input  wire rst,
    output wire [31:0] digest
);
    localparam integer A_GROUPS = N / A_FANOUT;
    localparam integer B_GROUPS = N / B_FANOUT;

    reg [7:0] counter;

    // Group-distinct source values prevent the replicated distribution
    // networks from being legally collapsed back into one broadcast net.
    (* keep *) reg signed [PRECISION-1:0] a_source [0:N*A_GROUPS-1];
    (* keep *) reg signed [PRECISION-1:0] b_source [0:N*B_GROUPS-1];

    integer i;
    integer g;
    always @(posedge clk) begin
        if (rst) begin
            counter <= 0;
            for (i = 0; i < N; i = i + 1) begin
                for (g = 0; g < A_GROUPS; g = g + 1)
                    a_source[i*A_GROUPS+g] <= i + 3*g + 1;
                for (g = 0; g < B_GROUPS; g = g + 1)
                    b_source[i*B_GROUPS+g] <= i - 5*g - 1;
            end
        end else begin
            counter <= counter + 1'b1;
            for (i = 0; i < N; i = i + 1) begin
                for (g = 0; g < A_GROUPS; g = g + 1)
                    a_source[i*A_GROUPS+g] <= $signed(counter) + i + 3*g + 1;
                for (g = 0; g < B_GROUPS; g = g + 1)
                    b_source[i*B_GROUPS+g] <= $signed(counter) - i - 5*g - 1;
            end
        end
    end

    wire [N*N*ACC_WIDTH-1:0] acc_flat;

    genvar r, c;
    generate
        for (r = 0; r < N; r = r + 1) begin : g_row
            for (c = 0; c < N; c = c + 1) begin : g_col
                localparam integer A_INDEX = r*A_GROUPS + (c/A_FANOUT);
                localparam integer B_INDEX = c*B_GROUPS + (r/B_FANOUT);

                wire signed [2*PRECISION-1:0] product;
                wire signed [ACC_WIDTH-1:0] product_ext;
                (* keep *) reg signed [ACC_WIDTH-1:0] accumulator;

                assign product = a_source[A_INDEX] * b_source[B_INDEX];
                assign product_ext =
                    {{(ACC_WIDTH-2*PRECISION){product[2*PRECISION-1]}}, product};

                always @(posedge clk) begin
                    if (rst)
                        accumulator <= {ACC_WIDTH{1'b0}};
                    else
                        accumulator <= accumulator + product_ext;
                end

                assign acc_flat[(r*N+c)*ACC_WIDTH +: ACC_WIDTH] = accumulator;
            end
        end
    endgenerate

    assign digest =
        acc_flat[0 +: 32] ^
        acc_flat[(N*N-1)*ACC_WIDTH +: 32];
endmodule
