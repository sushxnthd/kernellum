export PLATFORM = nangate45
export DESIGN_NAME = similarity_asic_transfer_blocal
export VERILOG_FILES = \
    /work/rtl/kernellum_local_mac_array.sv \
    /work/rtl/kernellum_blocal_mac_array.sv \
    /work/rtl/similarity_asic_transfer_blocal.sv
export SDC_FILE = /work/asic/transfer/constraints.sdc
export CORE_UTILIZATION = 35
export PLACE_DENSITY = 0.50
export TNS_END_PERCENT = 100
export LEC_CHECK = 0
export SKIP_CTS_REPAIR_TIMING = 1
export CAP_MARGIN = 30
export SLEW_MARGIN = 25
