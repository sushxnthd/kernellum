export PLATFORM = sky130hd
export DESIGN_NAME = similarity_asic_broadcast_canary

export VERILOG_FILES = \
    /work/rtl/similarity_broadcast_fabric.sv \
    /work/rtl/similarity_local_fabric.sv \
    /work/rtl/similarity_asic_canary.sv

export SDC_FILE = /work/asic/canary/constraints.sdc
export CORE_UTILIZATION = 35
export PLACE_DENSITY = 0.50
export TNS_END_PERCENT = 100
