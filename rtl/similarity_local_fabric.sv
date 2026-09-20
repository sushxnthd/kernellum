`timescale 1ns/1ps

module similarity_local_fabric #(
    parameter integer ROWS = 5,
    parameter integer COLS = 5,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire clk,
    input  wire rst,
    output wire [31:0] digest
);
    reg [7:0] counter;
    (* keep *) reg signed [PRECISION-1:0] a_edge [0:ROWS-1];
    (* keep *) reg signed [PRECISION-1:0] b_edge [0:COLS-1];

    integer i;
    always @(posedge clk) begin
        if (rst) begin
            counter <= 0;
            for (i = 0; i < ROWS; i = i + 1)
                a_edge[i] <= i + 1;
            for (i = 0; i < COLS; i = i + 1)
                b_edge[i] <= i + 2;
        end else begin
            counter <= counter + 1'b1;
            for (i = 0; i < ROWS; i = i + 1)
                a_edge[i] <= $signed(counter) + i + 1;
            for (i = 0; i < COLS; i = i + 1)
                b_edge[i] <= $signed(counter) - i - 1;
        end
    end

    wire [ROWS*COLS*ACC_WIDTH-1:0] acc_flat;

    genvar r, c;
    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_row
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                (* keep *) reg signed [PRECISION-1:0] a_local;
                (* keep *) reg signed [PRECISION-1:0] b_local;
                wire signed [2*PRECISION-1:0] product;
                wire signed [ACC_WIDTH-1:0] product_ext;
                (* keep *) reg signed [ACC_WIDTH-1:0] accumulator;

                assign product = a_local * b_local;
                assign product_ext =
                    {{(ACC_WIDTH-2*PRECISION){product[2*PRECISION-1]}}, product};

                always @(posedge clk) begin
                    if (rst) begin
                        a_local <= {PRECISION{1'b0}};
                        b_local <= {PRECISION{1'b0}};
                        accumulator <= {ACC_WIDTH{1'b0}};
                    end else begin
                        if (c == 0)
                            a_local <= a_edge[r];
                        else
                            a_local <= g_row[r].g_col[c-1].a_local;

                        if (r == 0)
                            b_local <= b_edge[c];
                        else
                            b_local <= g_row[r-1].g_col[c].b_local;

                        accumulator <= accumulator + product_ext;
                    end
                end

                assign acc_flat[(r*COLS+c)*ACC_WIDTH +: ACC_WIDTH] = accumulator;
            end
        end
    endgenerate

    assign digest =
        acc_flat[0 +: 32] ^
        acc_flat[(ROWS*COLS-1)*ACC_WIDTH +: 32];
endmodule
