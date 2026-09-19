`timescale 1ns/1ps

module kernellum_k2_board_top #(
    parameter integer ROWS = 8,
    parameter integer COLS = 8,
    parameter integer K_TILE = 32,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32,
    parameter integer CLOCK_HZ = 12_000_000,
    parameter integer BAUD = 115200,
    parameter integer K_ADDR_W = (K_TILE <= 1) ? 1 : $clog2(K_TILE),
    parameter integer K_LEN_W = (K_TILE <= 1) ? 1 : $clog2(K_TILE + 1),
    parameter integer ROW_W = (ROWS <= 1) ? 1 : $clog2(ROWS),
    parameter integer COL_W = (COLS <= 1) ? 1 : $clog2(COLS)
) (
    input  wire clk12,
    input  wire uart_rx,
    output wire uart_tx,
    output wire led_ready,
    output wire led_busy
);
    localparam [7:0] CMD_PING       = 8'h01;
    localparam [7:0] CMD_INFO       = 8'h02;
    localparam [7:0] CMD_LOAD_A     = 8'h10;
    localparam [7:0] CMD_LOAD_B     = 8'h11;
    localparam [7:0] CMD_RUN        = 8'h20;
    localparam [7:0] CMD_READ_CELL  = 8'h30;
    localparam [7:0] CMD_READ_CYCLES= 8'h31;
    localparam [7:0] ACK            = 8'hA5;
    localparam [7:0] ERR            = 8'hE0;

    localparam [3:0] P_IDLE      = 4'd0;
    localparam [3:0] P_A_ADDR    = 4'd1;
    localparam [3:0] P_A_DATA    = 4'd2;
    localparam [3:0] P_B_ADDR    = 4'd3;
    localparam [3:0] P_B_DATA    = 4'd4;
    localparam [3:0] P_RUN_K     = 4'd5;
    localparam [3:0] P_RUN_FLAGS = 4'd6;
    localparam [3:0] P_RUN_WAIT  = 4'd7;
    localparam [3:0] P_CELL_ROW  = 4'd8;
    localparam [3:0] P_CELL_COL  = 4'd9;

    reg [7:0] por = 0;
    always @(posedge clk12)
        if (!por[7])
            por <= por + 1'b1;
    wire rst = !por[7];

    wire [7:0] rx_byte;
    wire rx_valid;
    reg [7:0] tx_byte;
    reg tx_start;
    wire tx_busy;

    kernellum_uart_rx #(.CLOCK_HZ(CLOCK_HZ), .BAUD(BAUD)) u_rx (
        .clk(clk12), .rst(rst), .rx(uart_rx), .data(rx_byte), .valid(rx_valid)
    );

    kernellum_uart_tx #(.CLOCK_HZ(CLOCK_HZ), .BAUD(BAUD)) u_tx (
        .clk(clk12), .rst(rst), .data(tx_byte), .start(tx_start), .tx(uart_tx), .busy(tx_busy)
    );

    reg a_we, b_we, engine_start, clear_before;
    reg [K_ADDR_W-1:0] a_waddr, b_waddr;
    reg [ROWS*PRECISION-1:0] a_wdata;
    reg [COLS*PRECISION-1:0] b_wdata;
    reg [K_LEN_W-1:0] run_k_len;

    wire engine_busy, engine_done;
    wire [ROWS*COLS*ACC_WIDTH-1:0] acc_flat;

    kernellum_gemm_engine #(
        .ROWS(ROWS),
        .COLS(COLS),
        .PRECISION(PRECISION),
        .ACC_WIDTH(ACC_WIDTH),
        .K_TILE(K_TILE)
    ) u_engine (
        .clk(clk12),
        .rst(rst),
        .a_we(a_we),
        .a_waddr(a_waddr),
        .a_wdata(a_wdata),
        .b_we(b_we),
        .b_waddr(b_waddr),
        .b_wdata(b_wdata),
        .start(engine_start),
        .clear_before(clear_before),
        .k_len(run_k_len),
        .busy(engine_busy),
        .done(engine_done),
        .acc_flat(acc_flat)
    );

    assign led_ready = !rst;
    assign led_busy = engine_busy;

    reg [3:0] parser_state;
    reg [7:0] byte_index;
    reg [7:0] cell_row, cell_col;

    reg [31:0] busy_cycles;
    reg [31:0] last_cycles;
    reg measuring;

    reg [7:0] response [0:7];
    reg [3:0] response_len;
    reg [3:0] response_pos;
    reg response_active;

    wire [31:0] selected_cell =
        acc_flat[((cell_row * COLS + cell_col) * ACC_WIDTH) +: ACC_WIDTH];

    task queue_ack1;
        input [7:0] value;
        begin
            response[0] <= ACK;
            response[1] <= value;
            response_len <= 2;
            response_pos <= 0;
            response_active <= 1;
        end
    endtask

    task queue_ack32;
        input [31:0] value;
        begin
            response[0] <= ACK;
            response[1] <= value[7:0];
            response[2] <= value[15:8];
            response[3] <= value[23:16];
            response[4] <= value[31:24];
            response_len <= 5;
            response_pos <= 0;
            response_active <= 1;
        end
    endtask

    integer ai;
    integer bi;

    always @(posedge clk12) begin
        if (rst) begin
            tx_byte <= 0;
            tx_start <= 0;
            a_we <= 0;
            b_we <= 0;
            engine_start <= 0;
            clear_before <= 1;
            a_waddr <= 0;
            b_waddr <= 0;
            a_wdata <= 0;
            b_wdata <= 0;
            run_k_len <= 1;
            parser_state <= P_IDLE;
            byte_index <= 0;
            cell_row <= 0;
            cell_col <= 0;
            busy_cycles <= 0;
            last_cycles <= 0;
            measuring <= 0;
            response_len <= 0;
            response_pos <= 0;
            response_active <= 0;
            for (ai = 0; ai < 8; ai = ai + 1)
                response[ai] <= 0;
        end else begin
            tx_start <= 0;
            a_we <= 0;
            b_we <= 0;
            engine_start <= 0;

            if (measuring) begin
                if (engine_busy)
                    busy_cycles <= busy_cycles + 1'b1;
                if (engine_done) begin
                    last_cycles <= busy_cycles;
                    measuring <= 0;
                    queue_ack32(busy_cycles);
                    parser_state <= P_IDLE;
                end
            end

            if (response_active && !tx_busy && !tx_start) begin
                tx_byte <= response[response_pos];
                tx_start <= 1;
                if (response_pos + 1 >= response_len) begin
                    response_active <= 0;
                    response_pos <= 0;
                end else begin
                    response_pos <= response_pos + 1'b1;
                end
            end

            if (rx_valid && !response_active && !tx_busy && parser_state != P_RUN_WAIT) begin
                case (parser_state)
                    P_IDLE: begin
                        case (rx_byte)
                            CMD_PING: begin
                                response[0] <= ACK;
                                response[1] <= 8'h4B;
                                response[2] <= 8'h32;
                                response_len <= 3;
                                response_pos <= 0;
                                response_active <= 1;
                            end

                            CMD_INFO: begin
                                response[0] <= ACK;
                                response[1] <= ROWS[7:0];
                                response[2] <= COLS[7:0];
                                response[3] <= K_TILE[7:0];
                                response[4] <= 8'd12;
                                response_len <= 5;
                                response_pos <= 0;
                                response_active <= 1;
                            end

                            CMD_LOAD_A: parser_state <= P_A_ADDR;
                            CMD_LOAD_B: parser_state <= P_B_ADDR;
                            CMD_RUN: parser_state <= P_RUN_K;
                            CMD_READ_CELL: parser_state <= P_CELL_ROW;
                            CMD_READ_CYCLES: queue_ack32(last_cycles);

                            default: begin
                                response[0] <= ERR;
                                response[1] <= rx_byte;
                                response_len <= 2;
                                response_pos <= 0;
                                response_active <= 1;
                            end
                        endcase
                    end

                    P_A_ADDR: begin
                        a_waddr <= rx_byte[K_ADDR_W-1:0];
                        byte_index <= 0;
                        parser_state <= P_A_DATA;
                    end

                    P_A_DATA: begin
                        a_wdata[byte_index*PRECISION +: PRECISION] <= rx_byte;
                        if (byte_index + 1 >= ROWS) begin
                            a_we <= 1;
                            parser_state <= P_IDLE;
                            queue_ack1(8'h10);
                        end else begin
                            byte_index <= byte_index + 1'b1;
                        end
                    end

                    P_B_ADDR: begin
                        b_waddr <= rx_byte[K_ADDR_W-1:0];
                        byte_index <= 0;
                        parser_state <= P_B_DATA;
                    end

                    P_B_DATA: begin
                        b_wdata[byte_index*PRECISION +: PRECISION] <= rx_byte;
                        if (byte_index + 1 >= COLS) begin
                            b_we <= 1;
                            parser_state <= P_IDLE;
                            queue_ack1(8'h11);
                        end else begin
                            byte_index <= byte_index + 1'b1;
                        end
                    end

                    P_RUN_K: begin
                        run_k_len <= rx_byte[K_LEN_W-1:0];
                        parser_state <= P_RUN_FLAGS;
                    end

                    P_RUN_FLAGS: begin
                        clear_before <= rx_byte[0];
                        busy_cycles <= 0;
                        measuring <= 1;
                        engine_start <= 1;
                        parser_state <= P_RUN_WAIT;
                    end

                    P_CELL_ROW: begin
                        cell_row <= rx_byte;
                        parser_state <= P_CELL_COL;
                    end

                    P_CELL_COL: begin
                        cell_col <= rx_byte;
                        if (cell_row < ROWS && rx_byte < COLS) begin
                            response[0] <= ACK;
                            response[1] <= selected_cell[7:0];
                            response[2] <= selected_cell[15:8];
                            response[3] <= selected_cell[23:16];
                            response[4] <= selected_cell[31:24];
                            response_len <= 5;
                            response_pos <= 0;
                            response_active <= 1;
                        end else begin
                            response[0] <= ERR;
                            response[1] <= 8'h30;
                            response_len <= 2;
                            response_pos <= 0;
                            response_active <= 1;
                        end
                        parser_state <= P_IDLE;
                    end

                    default: parser_state <= P_IDLE;
                endcase
            end
        end
    end
endmodule
