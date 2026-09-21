`timescale 1ns/1ps

`ifndef SIM_ROWS
`define SIM_ROWS 2
`endif

`ifndef SIM_COLS
`define SIM_COLS 4
`endif

module tb_similarity_asic_transport_equivalence;
    localparam integer ROWS = `SIM_ROWS;
    localparam integer COLS = `SIM_COLS;
    localparam integer P = 8;
    localparam integer ACC = 32;
    localparam integer K_TILE = 8;
    localparam integer K_ADDR_W = $clog2(K_TILE);
    localparam integer K_LEN_W = $clog2(K_TILE + 1);

    reg clk = 0;
    reg rst = 1;
    reg a_we = 0;
    reg [K_ADDR_W-1:0] a_waddr = 0;
    reg [ROWS*P-1:0] a_wdata = 0;
    reg b_we = 0;
    reg [K_ADDR_W-1:0] b_waddr = 0;
    reg [COLS*P-1:0] b_wdata = 0;
    reg start = 0;
    reg clear_before = 1;
    reg [K_LEN_W-1:0] k_len = 0;

    wire broadcast_done;
    wire local_done;
    wire [ROWS*COLS*ACC-1:0] broadcast_acc;
    wire [ROWS*COLS*ACC-1:0] local_acc;

    integer expected [0:ROWS-1][0:COLS-1];
    integer rr;
    integer cc;
    integer kk;

    kernellum_gemm_engine #(
        .ROWS(ROWS), .COLS(COLS), .PRECISION(P), .ACC_WIDTH(ACC),
        .K_TILE(K_TILE), .TRANSPORT(0)
    ) broadcast_dut (
        .clk(clk), .rst(rst),
        .a_we(a_we), .a_waddr(a_waddr), .a_wdata(a_wdata),
        .b_we(b_we), .b_waddr(b_waddr), .b_wdata(b_wdata),
        .start(start), .clear_before(clear_before), .k_len(k_len),
        .busy(), .done(broadcast_done), .acc_flat(broadcast_acc)
    );

    kernellum_gemm_engine #(
        .ROWS(ROWS), .COLS(COLS), .PRECISION(P), .ACC_WIDTH(ACC),
        .K_TILE(K_TILE), .TRANSPORT(1)
    ) local_dut (
        .clk(clk), .rst(rst),
        .a_we(a_we), .a_waddr(a_waddr), .a_wdata(a_wdata),
        .b_we(b_we), .b_waddr(b_waddr), .b_wdata(b_wdata),
        .start(start), .clear_before(clear_before), .k_len(k_len),
        .busy(), .done(local_done), .acc_flat(local_acc)
    );

    always #5 clk = ~clk;

    function automatic signed [7:0] a_value;
        input integer phase;
        input integer k;
        input integer row;
        integer value;
        begin
            if (phase == 0)
                value = ((7*k + 11*row + 3) % 31) - 15;
            else
                value = ((5*k + 3*row + 1) % 13) - 6;
            a_value = value;
        end
    endfunction

    function automatic signed [7:0] b_value;
        input integer phase;
        input integer k;
        input integer col;
        integer value;
        begin
            if (phase == 0)
                value = ((5*k + 13*col + 7) % 29) - 14;
            else
                value = ((7*k + 2*col + 4) % 11) - 5;
            b_value = value;
        end
    endfunction

    task load_entry;
        input integer index;
        input integer phase;
        integer row;
        integer col;
        begin
            @(negedge clk);
            a_we = 1'b1;
            b_we = 1'b1;
            a_waddr = index[K_ADDR_W-1:0];
            b_waddr = index[K_ADDR_W-1:0];
            for (row = 0; row < ROWS; row = row + 1)
                a_wdata[row*P +: P] = a_value(phase, index, row);
            for (col = 0; col < COLS; col = col + 1)
                b_wdata[col*P +: P] = b_value(phase, index, col);
            @(negedge clk);
            a_we = 1'b0;
            b_we = 1'b0;
        end
    endtask

    task launch;
        input integer length;
        input integer do_clear;
        begin
            @(negedge clk);
            k_len = length[K_LEN_W-1:0];
            clear_before = do_clear[0];
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            wait(broadcast_done === 1'b1);
            wait(local_done === 1'b1);
            @(negedge clk);
        end
    endtask

    task check_all;
        integer row;
        integer col;
        reg signed [ACC-1:0] broadcast_value;
        reg signed [ACC-1:0] local_value;
        begin
            for (row = 0; row < ROWS; row = row + 1) begin
                for (col = 0; col < COLS; col = col + 1) begin
                    broadcast_value = broadcast_acc[(row*COLS+col)*ACC +: ACC];
                    local_value = local_acc[(row*COLS+col)*ACC +: ACC];
                    if (broadcast_value !== expected[row][col] ||
                        local_value !== expected[row][col] ||
                        broadcast_value !== local_value) begin
                        $display("FAIL ASIC TRANSFER EQUIVALENCE %0dx%0d [%0d,%0d]: b=%0d l=%0d expected=%0d",
                            ROWS, COLS, row, col, broadcast_value, local_value,
                            expected[row][col]);
                        $fatal(1);
                    end
                end
            end
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst = 0;

        for (rr = 0; rr < ROWS; rr = rr + 1)
            for (cc = 0; cc < COLS; cc = cc + 1)
                expected[rr][cc] = 0;

        for (kk = 0; kk < K_TILE; kk = kk + 1) begin
            load_entry(kk, 0);
            for (rr = 0; rr < ROWS; rr = rr + 1)
                for (cc = 0; cc < COLS; cc = cc + 1)
                    expected[rr][cc] = expected[rr][cc] +
                        $signed(a_value(0, kk, rr)) * $signed(b_value(0, kk, cc));
        end
        launch(K_TILE, 1);
        check_all();

        for (kk = 0; kk < 3; kk = kk + 1) begin
            load_entry(kk, 1);
            for (rr = 0; rr < ROWS; rr = rr + 1)
                for (cc = 0; cc < COLS; cc = cc + 1)
                    expected[rr][cc] = expected[rr][cc] +
                        $signed(a_value(1, kk, rr)) * $signed(b_value(1, kk, cc));
        end
        launch(3, 0);
        check_all();

        $display("KERNELLUM_ASIC_TRANSFER_EQUIVALENCE_PASS %0dx%0d", ROWS, COLS);
        $finish;
    end
endmodule
