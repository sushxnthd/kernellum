set clk_name clk
set clk_port_name clk

# ASAP7 reference constraints are expressed in picoseconds.  This relaxed
# canary target qualifies the flow; it is not a scientific measurement.
set clk_period 1000
set in2reg_max 200
set reg2out_max 200
set in2out_max 200

source $::env(PLATFORM_DIR)/constraints.sdc
