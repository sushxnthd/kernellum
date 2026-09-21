set clk_name clk
set clk_port_name clk
set clk_period 10.0

create_clock -name $clk_name -period $clk_period [get_ports $clk_port_name]
set_input_delay 0.0 -clock $clk_name [get_ports rst]
set_output_delay 0.0 -clock $clk_name [all_outputs]
