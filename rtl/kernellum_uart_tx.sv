`timescale 1ns/1ps

module kernellum_uart_tx #(
    parameter integer CLOCK_HZ = 12_000_000,
    parameter integer BAUD = 115200,
    parameter integer CLKS_PER_BIT = (CLOCK_HZ + BAUD/2) / BAUD,
    parameter integer COUNT_W = (CLKS_PER_BIT <= 2) ? 1 : $clog2(CLKS_PER_BIT + 1)
) (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] data,
    input  wire       start,
    output reg        tx,
    output reg        busy
);
    reg [9:0] frame;
    reg [3:0] bit_index;
    reg [COUNT_W-1:0] count;

    always @(posedge clk) begin
        if (rst) begin
            tx <= 1'b1;
            busy <= 1'b0;
            frame <= 10'h3ff;
            bit_index <= 0;
            count <= 0;
        end else begin
            if (!busy) begin
                tx <= 1'b1;
                count <= 0;
                bit_index <= 0;
                if (start) begin
                    frame <= {1'b1, data, 1'b0};
                    tx <= 1'b0;
                    busy <= 1'b1;
                end
            end else begin
                if (count == CLKS_PER_BIT-1) begin
                    count <= 0;
                    if (bit_index == 4'd9) begin
                        busy <= 1'b0;
                        tx <= 1'b1;
                        bit_index <= 0;
                    end else begin
                        bit_index <= bit_index + 1'b1;
                        tx <= frame[bit_index + 1'b1];
                    end
                end else begin
                    count <= count + 1'b1;
                end
            end
        end
    end
endmodule
