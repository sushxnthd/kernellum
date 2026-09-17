`timescale 1ns/1ps
module tb_kernellum_mlp_accel;
    localparam integer NS = 32;
    localparam integer IN0 = 64;
    localparam integer OUT = 10;
    logic clk = 0, rst = 1, start = 0, in_we = 0;
    logic [5:0] in_addr = 0;
    logic signed [7:0] in_data = 0;
    logic [3:0] out_addr = 0;
    logic signed [7:0] out_data;
    logic busy, done;
    integer s, i, j, errors;
    logic signed [7:0] golden_inputs [0:NS*IN0-1];
    logic signed [7:0] golden_outputs [0:NS*OUT-1];

    kernellum_mlp_accel dut(
        .clk(clk), .rst(rst), .start(start), .in_we(in_we), .in_addr(in_addr), .in_data(in_data),
        .out_addr(out_addr), .out_data(out_data), .busy(busy), .done(done)
    );
    always #5 clk = ~clk;

    initial begin
        $readmemh("weights/golden_inputs.hex", golden_inputs);
        $readmemh("weights/golden_outputs.hex", golden_outputs);
        errors = 0;
        repeat (4) @(posedge clk);
        rst <= 0;
        for (s = 0; s < NS; s = s + 1) begin
            for (i = 0; i < IN0; i = i + 1) begin
                @(negedge clk);
                in_we <= 1; in_addr <= i[5:0]; in_data <= golden_inputs[s*IN0+i];
            end
            @(negedge clk); in_we <= 0; start <= 1;
            @(negedge clk); start <= 0;
            wait (done === 1'b1);
            for (j = 0; j < OUT; j = j + 1) begin
                out_addr = j[3:0]; #1;
                if ($signed(out_data) !== $signed(golden_outputs[s*OUT+j])) begin
                    $display("MISMATCH sample=%0d out=%0d got=%0d exp=%0d", s, j, $signed(out_data), $signed(golden_outputs[s*OUT+j]));
                    errors = errors + 1;
                end
            end
            @(posedge clk);
        end
        if (errors == 0) begin
            $display("KERNELLUM_RTL_PASS samples=%0d", NS); $finish;
        end else begin
            $display("KERNELLUM_RTL_FAIL errors=%0d", errors); $fatal(1);
        end
    end
endmodule
