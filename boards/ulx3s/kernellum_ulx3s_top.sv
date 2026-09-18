`timescale 1ns/1ps
module kernellum_ulx3s_top #(
    parameter int LANES = 4
)(
    input  logic       clk_25mhz,
    input  logic [1:0] btn,
    output logic [7:0] led,
    output logic       gp0,
    output logic       gn0
);
    logic rst;
    logic start_meta, start_sync, start_prev, start_pulse;
    logic [3:0] class_led;
    logic done_led;

    assign rst = ~btn[0];

    // Synchronize and edge-detect FIRE1 so a held button produces one inference.
    always_ff @(posedge clk_25mhz) begin
        if (rst) begin
            start_meta <= 1'b0;
            start_sync <= 1'b0;
            start_prev <= 1'b0;
        end else begin
            start_meta <= btn[1];
            start_sync <= start_meta;
            start_prev <= start_sync;
        end
    end
    assign start_pulse = start_sync & ~start_prev;

    kernellum_demo_top #(.LANES(LANES)) demo(
        .clk(clk_25mhz),
        .rst(rst),
        .start_btn(start_pulse),
        .class_led(class_led),
        .done_led(done_led)
    );

    always_comb begin
        led = 8'b0;
        led[3:0] = class_led;
        led[4] = done_led;
    end

    // Logic-analyzer markers: gp0=start pulse, gn0=completion pulse.
    assign gp0 = start_pulse;
    assign gn0 = done_led;
endmodule
