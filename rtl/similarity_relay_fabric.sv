`timescale 1ns/1ps

module similarity_relay_fabric #(
    parameter integer N = 8,
    parameter integer RELAY_FANOUT = 2,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire clk,
    input  wire rst,
    output wire [31:0] digest
);
    localparam integer GROUPS = N / RELAY_FANOUT;

    reg [7:0] counter;
    (* keep *) reg signed [PRECISION-1:0] a_source [0:N-1];
    (* keep *) reg signed [PRECISION-1:0] b_source [0:N-1];

    (* keep *) reg signed [PRECISION-1:0] a_relay [0:N*GROUPS-1];
    (* keep *) reg signed [PRECISION-1:0] b_relay [0:N*GROUPS-1];

    integer i;
    integer g;
    always @(posedge clk) begin
        if (rst) begin
            counter <= 0;
            for (i = 0; i < N; i = i + 1) begin
                a_source[i] <= i + 1;
                b_source[i] <= i + 2;
                for (g = 0; g < GROUPS; g = g + 1) begin
                    a_relay[i*GROUPS+g] <= 0;
                    b_relay[i*GROUPS+g] <= 0;
                end
            end
        end else begin
            counter <= counter + 1'b1;
            for (i = 0; i < N; i = i + 1) begin
                a_source[i] <= $signed(counter) + i + 1;
                b_source[i] <= $signed(counter) - i - 1;
                for (g = 0; g < GROUPS; g = g + 1) begin
                    a_relay[i*GROUPS+g] <= a_source[i];
                    b_relay[i*GROUPS+g] <= b_source[i];
                end
            end
        end
    end

    wire [N*N*ACC_WIDTH-1:0] acc_flat;

    genvar r,c;
    generate
        for (r=0;r<N;r=r+1) begin : g_row
            for (c=0;c<N;c=c+1) begin : g_col
                localparam integer AG = c / RELAY_FANOUT;
                localparam integer BG = r / RELAY_FANOUT;
                wire signed [2*PRECISION-1:0] product;
                wire signed [ACC_WIDTH-1:0] product_ext;
                (* keep *) reg signed [ACC_WIDTH-1:0] accumulator;

                assign product =
                    a_relay[r*GROUPS+AG] *
                    b_relay[c*GROUPS+BG];

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
