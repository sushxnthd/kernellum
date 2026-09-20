`timescale 1ns/1ps

module tb_kernellum_transport_equivalence;
    localparam integer ROWS = 2;
    localparam integer COLS = 3;
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

    wire broadcast_done;
    wire local_done;
    wire [ROWS*COLS*ACC-1:0] broadcast_acc;
    wire [ROWS*COLS*ACC-1:0] local_acc;

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

    function automatic signed [ACC-1:0] read_broadcast(input integer rr, input integer cc);
        begin
            read_broadcast = broadcast_acc[(rr*COLS+cc)*ACC +: ACC];
        end
    endfunction

    function automatic signed [ACC-1:0] read_local(input integer rr, input integer cc);
        begin
            read_local = local_acc[(rr*COLS+cc)*ACC +: ACC];
        end
    endfunction

    task load_k;
        input integer idx;
        input signed [7:0] a0;
        input signed [7:0] a1;
        input signed [7:0] b0;
        input signed [7:0] b1;
        input signed [7:0] b2;
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
            b_wdata[16 +: 8] = b2;
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
            wait(broadcast_done === 1'b1);
            wait(local_done === 1'b1);
            @(negedge clk);
        end
    endtask

    task check_cell;
        input integer rr;
        input integer cc;
        input signed [ACC-1:0] expected;
        begin
            if (read_broadcast(rr, cc) !== expected ||
                read_local(rr, cc) !== expected ||
                read_broadcast(rr, cc) !== read_local(rr, cc)) begin
                $display("FAIL TRANSPORT EQUIVALENCE [%0d,%0d]: b=%0d l=%0d expected=%0d",
                    rr, cc, read_broadcast(rr, cc), read_local(rr, cc), expected);
                $fatal(1);
            end
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst = 0;

        load_k(0,    1,   -2,   7,  -8,   9);
        load_k(1,   -3,    4, -10,  11, -12);
        load_k(2,  127, -128,   2,  -3,   4);
        load_k(3,   -5,    6,  13,  14, -15);
        launch(4, 1);

        check_cell(0, 0,  226);
        check_cell(0, 1, -492);
        check_cell(0, 2,  628);
        check_cell(1, 0, -232);
        check_cell(1, 1,  528);
        check_cell(1, 2, -668);

        load_k(0, -7, 8, 9, -10, 11);
        launch(1, 0);

        check_cell(0, 0,  163);
        check_cell(0, 1, -422);
        check_cell(0, 2,  551);
        check_cell(1, 0, -160);
        check_cell(1, 1,  448);
        check_cell(1, 2, -580);

        $display("KERNELLUM_K1_TRANSPORT_EQUIVALENCE_PASS");
        $finish;
    end
endmodule
