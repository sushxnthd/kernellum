export PLATFORM = asap7
export DESIGN_NAME = similarity_asic_broadcast_canary

export VERILOG_FILES = \
    /work/rtl/similarity_broadcast_fabric.sv \
    /work/rtl/similarity_local_fabric.sv \
    /work/rtl/similarity_asic_canary.sv

export SDC_FILE = /work/asic/canary/constraints_asap7.sdc
export CORNER = BC
export CORE_UTILIZATION = 35
export PLACE_DENSITY = 0.50
export SKIP_LAST_GASP = 1
