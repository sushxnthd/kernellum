`timescale 1ns/1ps

module tb_kernellum_mac_array;
    localparam integer ROWS = 2;
    localparam integer COLS = 2;
    localparam integer P = 8;
    localparam integer ACC = 24;
    localparam integer BUFFER_KB = 1;
    localparam integer SCRATCH_WORDS = (BUFFER_KB * 1024) / 4;
    localparam integer ADDR_W = $clog2(SCRATCH_WORDS);

    reg clk = 0;
    reg rst = 1;
    reg clear_acc = 0;
    reg step = 0;
    reg [ROWS*P-1:0] a_vec = 0;
    reg [COLS*P-1:0] b_vec = 0;
    wire [ROWS*COLS*ACC-1:0] acc_flat;
    reg scratch_we = 0;
    reg [ADDR_W-1:0] scratch_addr = 0;
    reg [31:0] scratch_wdata = 0;
    wire [31:0] scratch_rdata;

    kernellum_mac_array #(
        .ROWS(ROWS), .COLS(COLS), .PRECISION(P), .ACC_WIDTH(ACC),
        .BUFFER_KB(BUFFER_KB), .DATAFLOW(0)
    ) dut (
        .clk(clk), .rst(rst), .clear_acc(clear_acc), .step(step),
        .a_vec(a_vec), .b_vec(b_vec), .acc_flat(acc_flat),
        .scratch_we(scratch_we), .scratch_addr(scratch_addr),
        .scratch_wdata(scratch_wdata), .scratch_rdata(scratch_rdata)
    );

    always #5 clk = ~clk;

    task drive_outer;
        input signed [7:0] a0;
        input signed [7:0] a1;
        input signed [7:0] b0;
        input signed [7:0] b1;
        begin
            @(negedge clk);
            a_vec[0 +: 8] = a0;
            a_vec[8 +: 8] = a1;
            b_vec[0 +: 8] = b0;
            b_vec[8 +: 8] = b1;
            step = 1;
            @(negedge clk);
            step = 0;
        end
    endtask

    function automatic signed [ACC-1:0] read_cell(input integer rr, input integer cc);
        begin
            read_cell = acc_flat[(rr*COLS+cc)*ACC +: ACC];
        end
    endfunction

    initial begin
        repeat (2) @(negedge clk);
        rst = 0;

        // A=[[1,2,3],[4,5,6]], B=[[7,8],[9,10],[11,12]]
        // Expected A*B=[[58,64],[139,154]].
        drive_outer(1, 4, 7, 8);
        drive_outer(2, 5, 9, 10);
        drive_outer(3, 6, 11, 12);

        @(negedge clk);
        if (read_cell(0,0) !== 58 || read_cell(0,1) !== 64 ||
            read_cell(1,0) !== 139 || read_cell(1,1) !== 154) begin
            $display("FAIL MAC: %0d %0d %0d %0d", read_cell(0,0), read_cell(0,1), read_cell(1,0), read_cell(1,1));
            $fatal(1);
        end

        scratch_addr = 7;
        scratch_wdata = 32'h4B305F35;
        scratch_we = 1;
        @(negedge clk);
        scratch_we = 0;
        @(posedge clk);
        #1;
        if (scratch_rdata !== 32'h4B305F35) begin
            $display("FAIL SCRATCH: %h", scratch_rdata);
            $fatal(1);
        end

        $display("KERNELLUM_RTL_SIM_PASS");
        $finish;
    end
endmodule
