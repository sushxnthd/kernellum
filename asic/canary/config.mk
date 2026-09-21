export PLATFORM = nangate45
export DESIGN_NAME = similarity_asic_broadcast_canary

export VERILOG_FILES = \
    /work/rtl/similarity_broadcast_fabric.sv \
    /work/rtl/similarity_local_fabric.sv \
    /work/rtl/similarity_asic_canary.sv

export SDC_FILE = /work/asic/canary/constraints.sdc
export CORE_UTILIZATION = 35
export PLACE_DENSITY = 0.50

# The pinned OpenROAD binary can terminate with SIGILL in the post-CTS
# repair/legalization block on some public runner CPUs. ORFS documents this
# switch for CI; final-route timing and DRC remain mandatory.
export SKIP_CTS_REPAIR_TIMING = 1
