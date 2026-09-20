`timescale 1ns/1ps

module kernellum_gemm_engine #(
    parameter integer ROWS = 4,
    parameter integer COLS = 4,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32,
    parameter integer K_TILE = 32,
    parameter integer TRANSPORT = 0,
    parameter integer K_ADDR_W = (K_TILE <= 1) ? 1 : $clog2(K_TILE),
    parameter integer K_LEN_W = (K_TILE <= 1) ? 1 : $clog2(K_TILE + 1)
) (
    input  wire                                clk,
    input  wire                                rst,

    input  wire                                a_we,
    input  wire [K_ADDR_W-1:0]                 a_waddr,
    input  wire [ROWS*PRECISION-1:0]           a_wdata,

    input  wire                                b_we,
    input  wire [K_ADDR_W-1:0]                 b_waddr,
    input  wire [COLS*PRECISION-1:0]           b_wdata,

    input  wire                                start,
    input  wire                                clear_before,
    input  wire [K_LEN_W-1:0]                  k_len,

    output wire                                busy,
    output wire                                done,
    output wire [ROWS*COLS*ACC_WIDTH-1:0]      acc_flat
);
    localparam [2:0] S_IDLE  = 3'd0;
    localparam [2:0] S_CLEAR = 3'd1;
    localparam [2:0] S_MAC   = 3'd2;
    localparam [2:0] S_DRAIN = 3'd3;
    localparam [2:0] S_DONE  = 3'd4;
    localparam integer LOCAL_DRAIN_CYCLES = ROWS + COLS - 1;
    localparam integer DRAIN_W =
        (LOCAL_DRAIN_CYCLES <= 1) ? 1 : $clog2(LOCAL_DRAIN_CYCLES + 1);

    (* ram_style = "block" *) reg [ROWS*PRECISION-1:0] a_tile [0:K_TILE-1];
    (* ram_style = "block" *) reg [COLS*PRECISION-1:0] b_tile [0:K_TILE-1];

    reg [2:0] state;
    reg [K_ADDR_W-1:0] k_idx;
    reg [K_LEN_W-1:0] active_k_len;
    reg [DRAIN_W-1:0] drain_count;

    wire [ROWS*PRECISION-1:0] a_vec = a_tile[k_idx];
    wire [COLS*PRECISION-1:0] b_vec = b_tile[k_idx];
    wire clear_acc = (state == S_CLEAR);
    wire step = (state == S_MAC);

    assign busy = (state != S_IDLE) && (state != S_DONE);
    assign done = (state == S_DONE);

    always @(posedge clk) begin
        if (a_we)
            a_tile[a_waddr] <= a_wdata;
        if (b_we)
            b_tile[b_waddr] <= b_wdata;

        if (rst) begin
            state <= S_IDLE;
            k_idx <= {K_ADDR_W{1'b0}};
            active_k_len <= {{(K_LEN_W-1){1'b0}}, 1'b1};
            drain_count <= {DRAIN_W{1'b0}};
        end else begin
            case (state)
                S_IDLE: begin
                    k_idx <= {K_ADDR_W{1'b0}};
                    drain_count <= {DRAIN_W{1'b0}};
                    if (start) begin
                        active_k_len <= (k_len == 0) ? {{(K_LEN_W-1){1'b0}}, 1'b1} : k_len;
                        if (clear_before)
                            state <= S_CLEAR;
                        else
                            state <= S_MAC;
                    end
                end

                S_CLEAR: begin
                    k_idx <= {K_ADDR_W{1'b0}};
                    state <= S_MAC;
                end

                S_MAC: begin
                    if ((k_idx + 1'b1) >= active_k_len) begin
                        if (TRANSPORT == 0) begin
                            state <= S_DONE;
                        end else begin
                            drain_count <= {DRAIN_W{1'b0}};
                            state <= S_DRAIN;
                        end
                    end else begin
                        k_idx <= k_idx + 1'b1;
                    end
                end

                S_DRAIN: begin
                    if ((drain_count + 1'b1) >= LOCAL_DRAIN_CYCLES)
                        state <= S_DONE;
                    else
                        drain_count <= drain_count + 1'b1;
                end

                S_DONE: begin
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    localparam integer DUMMY_SCRATCH_ADDR_W = 8;

    generate
        if (TRANSPORT == 0) begin : g_broadcast_transport
            kernellum_mac_array #(
                .ROWS(ROWS),
                .COLS(COLS),
                .PRECISION(PRECISION),
                .ACC_WIDTH(ACC_WIDTH),
                .BUFFER_KB(1),
                .DATAFLOW(1)
            ) u_mac_array (
                .clk(clk),
                .rst(rst),
                .clear_acc(clear_acc),
                .step(step),
                .a_vec(a_vec),
                .b_vec(b_vec),
                .acc_flat(acc_flat),
                .scratch_we(1'b0),
                .scratch_addr({DUMMY_SCRATCH_ADDR_W{1'b0}}),
                .scratch_wdata(32'b0),
                .scratch_rdata()
            );
        end else begin : g_local_transport
            kernellum_local_mac_array #(
                .ROWS(ROWS),
                .COLS(COLS),
                .PRECISION(PRECISION),
                .ACC_WIDTH(ACC_WIDTH)
            ) u_local_mac_array (
                .clk(clk),
                .rst(rst),
                .clear_acc(clear_acc),
                .step(step),
                .a_vec(a_vec),
                .b_vec(b_vec),
                .acc_flat(acc_flat)
            );
        end
    endgenerate
endmodule
