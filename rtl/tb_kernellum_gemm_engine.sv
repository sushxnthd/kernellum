`timescale 1ns/1ps

module tb_kernellum_gemm_engine;
    localparam integer ROWS = 2;
    localparam integer COLS = 2;
    localparam integer P = 8;
    localparam integer ACC = 24;
    localparam integer K_TILE = 4;
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

    wire busy;
    wire done;
    wire [ROWS*COLS*ACC-1:0] acc_flat;

    kernellum_gemm_engine #(
        .ROWS(ROWS), .COLS(COLS), .PRECISION(P), .ACC_WIDTH(ACC), .K_TILE(K_TILE)
    ) dut (
        .clk(clk), .rst(rst),
        .a_we(a_we), .a_waddr(a_waddr), .a_wdata(a_wdata),
        .b_we(b_we), .b_waddr(b_waddr), .b_wdata(b_wdata),
        .start(start), .clear_before(clear_before), .k_len(k_len),
        .busy(busy), .done(done), .acc_flat(acc_flat)
    );

    always #5 clk = ~clk;

    function automatic signed [ACC-1:0] read_cell(input integer rr, input integer cc);
        begin
            read_cell = acc_flat[(rr*COLS+cc)*ACC +: ACC];
        end
    endfunction

    task load_k;
        input integer idx;
        input signed [7:0] a0;
        input signed [7:0] a1;
        input signed [7:0] b0;
        input signed [7:0] b1;
        begin
            @(negedge clk);
            a_we = 1;
            b_we = 1;
            a_waddr = idx[K_ADDR_W-1:0];
            b_waddr = idx[K_ADDR_W-1:0];
            a_wdata[0 +: 8] = a0;
            a_wdata[8 +: 8] = a1;
            b_wdata[0 +: 8] = b0;
            b_wdata[8 +: 8] = b1;
            @(negedge clk);
            a_we = 0;
            b_we = 0;
        end
    endtask

    task launch;
        input integer len;
        input integer do_clear;
        begin
            @(negedge clk);
            k_len = len[K_LEN_W-1:0];
            clear_before = do_clear[0];
            start = 1;
            @(negedge clk);
            start = 0;
            wait(done === 1'b1);
            @(negedge clk);
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst = 0;

        // A=[[1,2,3],[4,5,6]], B=[[7,8],[9,10],[11,12]]
        load_k(0, 1, 4, 7, 8);
        load_k(1, 2, 5, 9, 10);
        load_k(2, 3, 6, 11, 12);
        launch(3, 1);

        if (read_cell(0,0) !== 58 || read_cell(0,1) !== 64 ||
            read_cell(1,0) !== 139 || read_cell(1,1) !== 154) begin
            $display("FAIL GEMM: %0d %0d %0d %0d",
                read_cell(0,0), read_cell(0,1), read_cell(1,0), read_cell(1,1));
            $fatal(1);
        end

        // Accumulate one more outer product of [1,1]^T * [1,1].
        load_k(0, 1, 1, 1, 1);
        launch(1, 0);

        if (read_cell(0,0) !== 59 || read_cell(0,1) !== 65 ||
            read_cell(1,0) !== 140 || read_cell(1,1) !== 155) begin
            $display("FAIL ACCUMULATE: %0d %0d %0d %0d",
                read_cell(0,0), read_cell(0,1), read_cell(1,0), read_cell(1,1));
            $fatal(1);
        end

        $display("KERNELLUM_K1_GEMM_SIM_PASS");
        $finish;
    end
endmodule
