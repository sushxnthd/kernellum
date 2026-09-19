`timescale 1ns/1ps

module tb_kernellum_k2_uart;
    localparam integer CLOCK_HZ = 12_000_000;
    localparam integer BAUD = 115200;
    localparam integer CLKS_PER_BIT = (CLOCK_HZ + BAUD/2) / BAUD;

    reg clk12 = 0;
    reg uart_rx = 1;
    wire uart_tx;
    wire led_ready;
    wire led_busy;

    kernellum_k2_board_top #(
        .ROWS(2),
        .COLS(2),
        .K_TILE(4),
        .CLOCK_HZ(CLOCK_HZ),
        .BAUD(BAUD)
    ) dut (
        .clk12(clk12),
        .uart_rx(uart_rx),
        .uart_tx(uart_tx),
        .led_ready(led_ready),
        .led_busy(led_busy)
    );

    always #5 clk12 = ~clk12;

    task wait_clocks;
        input integer n;
        integer q;
        begin
            for (q = 0; q < n; q = q + 1)
                @(posedge clk12);
        end
    endtask

    task send_byte;
        input [7:0] value;
        integer i;
        begin
            uart_rx = 0;
            wait_clocks(CLKS_PER_BIT);
            for (i = 0; i < 8; i = i + 1) begin
                uart_rx = value[i];
                wait_clocks(CLKS_PER_BIT);
            end
            uart_rx = 1;
            wait_clocks(CLKS_PER_BIT);
        end
    endtask

    task recv_byte;
        output [7:0] value;
        integer i;
        begin
            wait(uart_tx === 1'b0);
            wait_clocks(CLKS_PER_BIT + CLKS_PER_BIT/2);
            for (i = 0; i < 8; i = i + 1) begin
                value[i] = uart_tx;
                wait_clocks(CLKS_PER_BIT);
            end
            wait_clocks(CLKS_PER_BIT/2);
        end
    endtask

    reg [7:0] r0, r1, r2, r3, r4;

    initial begin
        wait(led_ready === 1'b1);
        wait_clocks(20);

        send_byte(8'h01);
        recv_byte(r0);
        recv_byte(r1);
        recv_byte(r2);
        if (r0 !== 8'hA5 || r1 !== 8'h4B || r2 !== 8'h32) begin
            $display("FAIL PING %02x %02x %02x", r0, r1, r2);
            $fatal(1);
        end

        send_byte(8'h02);
        recv_byte(r0);
        recv_byte(r1);
        recv_byte(r2);
        recv_byte(r3);
        recv_byte(r4);
        if (r0 !== 8'hA5 || r1 !== 2 || r2 !== 2 || r3 !== 4 || r4 !== 12) begin
            $display("FAIL INFO %02x %02x %02x %02x %02x", r0, r1, r2, r3, r4);
            $fatal(1);
        end

        $display("KERNELLUM_K2_UART_SIM_PASS");
        $finish;
    end
endmodule
