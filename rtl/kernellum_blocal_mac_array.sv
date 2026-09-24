`timescale 1ns/1ps

// Distinct B-local/A-sign-local intervention.
// A[6:0] and both valid streams retain stride-two transport. A[7] and all
// eight B bits are per-PE registers. Lane-diverse invalid reset states make
// adjacent data replicas sequentially non-equivalent under synthesis.
module kernellum_blocal_mac_array #(
    parameter integer ROWS = 8,
    parameter integer COLS = 8,
    parameter integer STRIDE = 2,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32,
    parameter integer ROW_GROUPS = (ROWS + STRIDE - 1) / STRIDE,
    parameter integer COL_GROUPS = (COLS + STRIDE - 1) / STRIDE
) (
    input  wire                           clk,
    input  wire                           rst,
    input  wire                           clear_acc,
    input  wire                           step,
    input  wire [ROWS*PRECISION-1:0]      a_vec,
    input  wire [COLS*PRECISION-1:0]      b_vec,
    output wire [ROWS*COLS*ACC_WIDTH-1:0] acc_flat
);
    localparam integer A_COMMON_BITS = PRECISION - 1;
    wire signed [PRECISION-1:0] a_edge [0:ROWS-1];
    wire signed [PRECISION-1:0] b_edge [0:COLS-1];
    wire a_edge_valid [0:ROWS-1];
    wire b_edge_valid [0:COLS-1];
    genvar r, c, g;

    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_a_edge
            kernellum_delay_line #(.WIDTH(PRECISION), .DELAY(r / STRIDE)) delay (
                .clk(clk), .rst(rst), .clear_pipe(clear_acc),
                .valid_in(step), .data_in(a_vec[r*PRECISION +: PRECISION]),
                .valid_out(a_edge_valid[r]), .data_out(a_edge[r])
            );
        end
        for (c = 0; c < COLS; c = c + 1) begin : g_b_edge
            kernellum_delay_line #(.WIDTH(PRECISION), .DELAY(c / STRIDE)) delay (
                .clk(clk), .rst(rst), .clear_pipe(clear_acc),
                .valid_in(step), .data_in(b_vec[c*PRECISION +: PRECISION]),
                .valid_out(b_edge_valid[c]), .data_out(b_edge[c])
            );
        end
    endgenerate

    wire signed [A_COMMON_BITS-1:0] a_common [0:ROWS-1][0:COL_GROUPS-1];
    wire a_valid [0:ROWS-1][0:COL_GROUPS-1];
    wire b_valid [0:ROW_GROUPS-1][0:COLS-1];
    wire a_sign_rep [0:ROWS-1][0:COLS-1];
    wire signed [PRECISION-1:0] b_rep [0:ROWS-1][0:COLS-1];

    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_a_common
            for (g = 0; g < COL_GROUPS; g = g + 1) begin : g_seg
                reg signed [A_COMMON_BITS-1:0] data_q;
                reg valid_q;
                if (g == 0) begin : first
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin data_q <= 0; valid_q <= 0; end
                        else begin
                            data_q <= a_edge[r][A_COMMON_BITS-1:0];
                            valid_q <= a_edge_valid[r];
                        end
                    end
                end else begin : next
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin data_q <= 0; valid_q <= 0; end
                        else begin
                            data_q <= a_common[r][g-1];
                            valid_q <= a_valid[r][g-1];
                        end
                    end
                end
                assign a_common[r][g] = data_q;
                assign a_valid[r][g] = valid_q;
            end
        end

        for (c = 0; c < COLS; c = c + 1) begin : g_b_valid
            for (g = 0; g < ROW_GROUPS; g = g + 1) begin : g_seg
                reg valid_q;
                if (g == 0) begin : first
                    always @(posedge clk) begin
                        if (rst || clear_acc) valid_q <= 0;
                        else valid_q <= b_edge_valid[c];
                    end
                end else begin : next
                    always @(posedge clk) begin
                        if (rst || clear_acc) valid_q <= 0;
                        else valid_q <= b_valid[g-1][c];
                    end
                end
                assign b_valid[g][c] = valid_q;
            end
        end

        for (r = 0; r < ROWS; r = r + 1) begin : g_a_rep
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                (* keep *) reg sign_q;
                always @(posedge clk) begin
                    if (rst || clear_acc) sign_q <= (c % STRIDE);
                    else if (c < STRIDE) sign_q <= a_edge[r][PRECISION-1];
                    else sign_q <= a_sign_rep[r][c-STRIDE];
                end
                assign a_sign_rep[r][c] = sign_q;
            end
        end

        for (r = 0; r < ROWS; r = r + 1) begin : g_b_rep
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                (* keep *) reg signed [PRECISION-1:0] data_q;
                always @(posedge clk) begin
                    if (rst || clear_acc)
                        data_q <= (r % STRIDE) ? {PRECISION{1'b1}} : {PRECISION{1'b0}};
                    else if (r < STRIDE)
                        data_q <= b_edge[c];
                    else
                        data_q <= b_rep[r-STRIDE][c];
                end
                assign b_rep[r][c] = data_q;
            end
        end

        for (r = 0; r < ROWS; r = r + 1) begin : g_row
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                wire signed [PRECISION-1:0] a_operand = {
                    a_sign_rep[r][c], a_common[r][c/STRIDE]
                };
                wire signed [2*PRECISION-1:0] product = a_operand * b_rep[r][c];
                wire signed [ACC_WIDTH-1:0] extended = {
                    {(ACC_WIDTH-2*PRECISION){product[2*PRECISION-1]}}, product
                };
                reg signed [ACC_WIDTH-1:0] accumulator;
                always @(posedge clk) begin
                    if (rst || clear_acc) accumulator <= 0;
                    else if (a_valid[r][c/STRIDE] && b_valid[r/STRIDE][c])
                        accumulator <= accumulator + extended;
                end
                assign acc_flat[(r*COLS+c)*ACC_WIDTH +: ACC_WIDTH] = accumulator;
            end
        end
    endgenerate
endmodule
