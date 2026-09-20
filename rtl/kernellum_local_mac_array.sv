`timescale 1ns/1ps

module kernellum_delay_line #(
    parameter integer WIDTH = 8,
    parameter integer DELAY = 0
) (
    input  wire                    clk,
    input  wire                    rst,
    input  wire                    clear_pipe,
    input  wire                    valid_in,
    input  wire signed [WIDTH-1:0] data_in,
    output wire                    valid_out,
    output wire signed [WIDTH-1:0] data_out
);
    generate
        if (DELAY == 0) begin : g_passthrough
            assign valid_out = valid_in;
            assign data_out = data_in;
        end else begin : g_delay
            reg signed [WIDTH-1:0] data_pipe [0:DELAY-1];
            reg                    valid_pipe [0:DELAY-1];
            integer i;

            always @(posedge clk) begin
                if (rst || clear_pipe) begin
                    for (i = 0; i < DELAY; i = i + 1) begin
                        data_pipe[i] <= {WIDTH{1'b0}};
                        valid_pipe[i] <= 1'b0;
                    end
                end else begin
                    data_pipe[0] <= data_in;
                    valid_pipe[0] <= valid_in;
                    for (i = 1; i < DELAY; i = i + 1) begin
                        data_pipe[i] <= data_pipe[i-1];
                        valid_pipe[i] <= valid_pipe[i-1];
                    end
                end
            end

            assign data_out = data_pipe[DELAY-1];
            assign valid_out = valid_pipe[DELAY-1];
        end
    endgenerate
endmodule

module kernellum_local_mac_array #(
    parameter integer ROWS = 8,
    parameter integer COLS = 8,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire                                clk,
    input  wire                                rst,
    input  wire                                clear_acc,
    input  wire                                step,
    input  wire [ROWS*PRECISION-1:0]           a_vec,
    input  wire [COLS*PRECISION-1:0]           b_vec,
    output wire [ROWS*COLS*ACC_WIDTH-1:0]      acc_flat
);
    wire signed [PRECISION-1:0] a_edge_data [0:ROWS-1];
    wire signed [PRECISION-1:0] b_edge_data [0:COLS-1];
    wire                         a_edge_valid [0:ROWS-1];
    wire                         b_edge_valid [0:COLS-1];

    genvar er, ec;
    generate
        for (er = 0; er < ROWS; er = er + 1) begin : g_a_skew
            kernellum_delay_line #(
                .WIDTH(PRECISION),
                .DELAY(er)
            ) u_a_delay (
                .clk(clk),
                .rst(rst),
                .clear_pipe(clear_acc),
                .valid_in(step),
                .data_in(a_vec[er*PRECISION +: PRECISION]),
                .valid_out(a_edge_valid[er]),
                .data_out(a_edge_data[er])
            );
        end

        for (ec = 0; ec < COLS; ec = ec + 1) begin : g_b_skew
            kernellum_delay_line #(
                .WIDTH(PRECISION),
                .DELAY(ec)
            ) u_b_delay (
                .clk(clk),
                .rst(rst),
                .clear_pipe(clear_acc),
                .valid_in(step),
                .data_in(b_vec[ec*PRECISION +: PRECISION]),
                .valid_out(b_edge_valid[ec]),
                .data_out(b_edge_data[ec])
            );
        end
    endgenerate

    genvar r, c;
    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_row
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                reg signed [PRECISION-1:0] a_local;
                reg signed [PRECISION-1:0] b_local;
                reg                         a_valid;
                reg                         b_valid;
                reg signed [ACC_WIDTH-1:0] accumulator;

                wire signed [PRECISION-1:0] a_in;
                wire signed [PRECISION-1:0] b_in;
                wire                         a_in_valid;
                wire                         b_in_valid;
                wire signed [2*PRECISION-1:0] product;
                wire signed [ACC_WIDTH-1:0] product_ext;

                if (c == 0) begin : g_a_edge
                    assign a_in = a_edge_data[r];
                    assign a_in_valid = a_edge_valid[r];
                end else begin : g_a_neighbor
                    assign a_in = g_row[r].g_col[c-1].a_local;
                    assign a_in_valid = g_row[r].g_col[c-1].a_valid;
                end

                if (r == 0) begin : g_b_edge
                    assign b_in = b_edge_data[c];
                    assign b_in_valid = b_edge_valid[c];
                end else begin : g_b_neighbor
                    assign b_in = g_row[r-1].g_col[c].b_local;
                    assign b_in_valid = g_row[r-1].g_col[c].b_valid;
                end

                assign product = a_local * b_local;
                assign product_ext =
                    {{(ACC_WIDTH-2*PRECISION){product[2*PRECISION-1]}}, product};

                always @(posedge clk) begin
                    if (rst || clear_acc) begin
                        a_local <= {PRECISION{1'b0}};
                        b_local <= {PRECISION{1'b0}};
                        a_valid <= 1'b0;
                        b_valid <= 1'b0;
                        accumulator <= {ACC_WIDTH{1'b0}};
                    end else begin
                        a_local <= a_in;
                        b_local <= b_in;
                        a_valid <= a_in_valid;
                        b_valid <= b_in_valid;
                        if (a_valid && b_valid)
                            accumulator <= accumulator + product_ext;
                    end
                end

                assign acc_flat[(r*COLS+c)*ACC_WIDTH +: ACC_WIDTH] = accumulator;
            end
        end
    endgenerate
endmodule
