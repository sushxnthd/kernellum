`timescale 1ns/1ps

module kernellum_uart_rx #(
    parameter integer CLOCK_HZ = 12_000_000,
    parameter integer BAUD = 115200,
    parameter integer CLKS_PER_BIT = (CLOCK_HZ + BAUD/2) / BAUD,
    parameter integer COUNT_W = (CLKS_PER_BIT <= 2) ? 1 : $clog2(CLKS_PER_BIT + 1)
) (
    input  wire       clk,
    input  wire       rst,
    input  wire       rx,
    output reg  [7:0] data,
    output reg        valid
);
    localparam [1:0] S_IDLE  = 2'd0;
    localparam [1:0] S_START = 2'd1;
    localparam [1:0] S_DATA  = 2'd2;
    localparam [1:0] S_STOP  = 2'd3;

    reg [1:0] state;
    reg [COUNT_W-1:0] count;
    reg [2:0] bit_index;
    reg [7:0] shift;
    reg rx_meta, rx_sync;

    always @(posedge clk) begin
        rx_meta <= rx;
        rx_sync <= rx_meta;

        if (rst) begin
            state <= S_IDLE;
            count <= 0;
            bit_index <= 0;
            shift <= 0;
            data <= 0;
            valid <= 0;
            rx_meta <= 1;
            rx_sync <= 1;
        end else begin
            valid <= 0;
            case (state)
                S_IDLE: begin
                    count <= 0;
                    if (!rx_sync)
                        state <= S_START;
                end

                S_START: begin
                    if (count == (CLKS_PER_BIT/2)) begin
                        if (!rx_sync) begin
                            count <= 0;
                            bit_index <= 0;
                            state <= S_DATA;
                        end else begin
                            state <= S_IDLE;
                        end
                    end else begin
                        count <= count + 1'b1;
                    end
                end

                S_DATA: begin
                    if (count == CLKS_PER_BIT-1) begin
                        count <= 0;
                        shift[bit_index] <= rx_sync;
                        if (bit_index == 3'd7) begin
                            bit_index <= 0;
                            state <= S_STOP;
                        end else begin
                            bit_index <= bit_index + 1'b1;
                        end
                    end else begin
                        count <= count + 1'b1;
                    end
                end

                S_STOP: begin
                    if (count == CLKS_PER_BIT-1) begin
                        count <= 0;
                        if (rx_sync) begin
                            data <= shift;
                            valid <= 1'b1;
                        end
                        state <= S_IDLE;
                    end else begin
                        count <= count + 1'b1;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
