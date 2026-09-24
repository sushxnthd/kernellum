`timescale 1ns/1ps
`ifndef TEST_ROWS
`define TEST_ROWS 5
`endif
`ifndef TEST_COLS
`define TEST_COLS 8
`endif

module tb_kernellum_criticalbit_equivalence;
    localparam integer ROWS = `TEST_ROWS;
    localparam integer COLS = `TEST_COLS;
    localparam integer PRECISION = 8;
    localparam integer ACC_WIDTH = 32;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst = 1;
    reg clear_acc = 1;
    reg step = 0;
    reg [ROWS*PRECISION-1:0] a_vec = 0;
    reg [COLS*PRECISION-1:0] b_vec = 0;
    wire [ROWS*COLS*ACC_WIDTH-1:0] full_acc;
    wire [ROWS*COLS*ACC_WIDTH-1:0] candidate_acc;

    kernellum_local_mac_array #(.ROWS(ROWS), .COLS(COLS)) full (
        .clk(clk), .rst(rst), .clear_acc(clear_acc), .step(step),
        .a_vec(a_vec), .b_vec(b_vec), .acc_flat(full_acc)
    );
    kernellum_selective_mac_array #(.ROWS(ROWS), .COLS(COLS)) candidate (
        .clk(clk), .rst(rst), .clear_acc(clear_acc), .step(step),
        .a_vec(a_vec), .b_vec(b_vec), .acc_flat(candidate_acc)
    );

    integer expected [0:ROWS*COLS-1];
    integer r, c, k, phase;
    task run_trial(input integer trial);
        begin
            for (r = 0; r < ROWS*COLS; r = r + 1)
                expected[r] = 0;
            for (k = 0; k < 5; k = k + 1) begin
                @(negedge clk);
                step = 1;
                for (r = 0; r < ROWS; r = r + 1)
                    a_vec[r*PRECISION +: PRECISION] = (k-r-2-trial);
                for (c = 0; c < COLS; c = c + 1)
                    b_vec[c*PRECISION +: PRECISION] = (3+k+c+trial);
                for (r = 0; r < ROWS; r = r + 1)
                    for (c = 0; c < COLS; c = c + 1)
                        expected[r*COLS+c] = expected[r*COLS+c] +
                            (k-r-2-trial)*(3+k+c+trial);
            end
            @(negedge clk);
            step = 0;
            repeat (ROWS + COLS + 5) @(posedge clk);
            #1;
            for (r = 0; r < ROWS; r = r + 1)
                for (c = 0; c < COLS; c = c + 1) begin
                    if ($signed(full_acc[(r*COLS+c)*ACC_WIDTH +: ACC_WIDTH]) !==
                        expected[r*COLS+c])
                        $fatal(1, "full local mismatch %0d,%0d",r,c);
                    if ($signed(candidate_acc[(r*COLS+c)*ACC_WIDTH +: ACC_WIDTH]) !==
                        expected[r*COLS+c])
                        $fatal(1, "critical-bit mismatch %0d,%0d",r,c);
                end
            @(negedge clk);
            clear_acc = 1;
            @(negedge clk);
            clear_acc = 0;
        end
    endtask

    initial begin
        repeat (2) @(negedge clk);
        rst = 0;
        clear_acc = 0;
        for (phase = 0; phase < 2; phase = phase + 1)
            run_trial(phase);
        $display("KERNELLUM_CRITICALBIT_EQUIVALENCE_PASS rows=%0d cols=%0d",
                 ROWS, COLS);
        $finish;
    end
endmodule
