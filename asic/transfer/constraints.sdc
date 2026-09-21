set clk_name clk
set clk_port_name clk
set clk_period 20.0

create_clock -name $clk_name -period $clk_period [get_ports $clk_port_name]
set_false_path -from [get_ports rst]
set_false_path -to [get_ports digest]
