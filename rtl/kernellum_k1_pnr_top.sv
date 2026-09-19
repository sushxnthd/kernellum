`timescale 1ns/1ps

module kernellum_k1_pnr_top #(
    parameter integer ROWS = 4,
    parameter integer COLS = 4,
    parameter integer K_TILE = 32,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32,
    parameter integer K_ADDR_W = (K_TILE <= 1) ? 1 : $clog2(K_TILE),
    parameter integer K_LEN_W = (K_TILE <= 1) ? 1 : $clog2(K_TILE + 1)
) (
    input  wire clk,
    input  wire rst,
    output wire done_out,
    output reg  [31:0] digest_out
);
    localparam [2:0] T_LOAD = 3'd0;
    localparam [2:0] T_START = 3'd1;
    localparam [2:0] T_WAIT = 3'd2;
    localparam [2:0] T_CAPTURE = 3'd3;
    localparam [2:0] T_RESTART = 3'd4;

    reg [2:0] top_state;
    reg [K_ADDR_W-1:0] load_idx;
    reg a_we;
    reg b_we;
    reg start;

    reg [ROWS*PRECISION-1:0] a_wdata;
    reg [COLS*PRECISION-1:0] b_wdata;

    wire busy;
    wire done;
    (* keep *) wire [ROWS*COLS*ACC_WIDTH-1:0] acc_flat;

    integer r;
    integer c;

    always @* begin
        a_wdata = {ROWS*PRECISION{1'b0}};
        b_wdata = {COLS*PRECISION{1'b0}};
        for (r = 0; r < ROWS; r = r + 1)
            a_wdata[r*PRECISION +: PRECISION] = load_idx + r + 1;
        for (c = 0; c < COLS; c = c + 1)
            b_wdata[c*PRECISION +: PRECISION] = (load_idx << 1) + c + 1;
    end

    assign done_out = done;

    always @(posedge clk) begin
        if (rst) begin
            top_state <= T_LOAD;
            load_idx <= {K_ADDR_W{1'b0}};
            a_we <= 1'b0;
            b_we <= 1'b0;
            start <= 1'b0;
            digest_out <= 32'b0;
        end else begin
            a_we <= 1'b0;
            b_we <= 1'b0;
            start <= 1'b0;

            case (top_state)
                T_LOAD: begin
                    a_we <= 1'b1;
                    b_we <= 1'b1;
                    if (load_idx == K_TILE-1) begin
                        load_idx <= {K_ADDR_W{1'b0}};
                        top_state <= T_START;
                    end else begin
                        load_idx <= load_idx + 1'b1;
                    end
                end

                T_START: begin
                    start <= 1'b1;
                    top_state <= T_WAIT;
                end

                T_WAIT: begin
                    if (done)
                        top_state <= T_CAPTURE;
                end

                T_CAPTURE: begin
                    digest_out <= digest_out ^ acc_flat[31:0];
                    top_state <= T_RESTART;
                end

                T_RESTART: begin
                    top_state <= T_LOAD;
                end

                default: top_state <= T_LOAD;
            endcase
        end
    end

    kernellum_gemm_engine #(
        .ROWS(ROWS),
        .COLS(COLS),
        .PRECISION(PRECISION),
        .ACC_WIDTH(ACC_WIDTH),
        .K_TILE(K_TILE)
    ) u_engine (
        .clk(clk),
        .rst(rst),
        .a_we(a_we),
        .a_waddr(load_idx),
        .a_wdata(a_wdata),
        .b_we(b_we),
        .b_waddr(load_idx),
        .b_wdata(b_wdata),
        .start(start),
        .clear_before(1'b1),
        .k_len(K_TILE[K_LEN_W-1:0]),
        .busy(busy),
        .done(done),
        .acc_flat(acc_flat)
    );
endmodule
