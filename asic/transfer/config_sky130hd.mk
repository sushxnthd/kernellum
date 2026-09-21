export PLATFORM = sky130hd
export DESIGN_NAME = similarity_asic_transfer_broadcast

export VERILOG_FILES = \
    /work/rtl/kernellum_mac_array.sv \
    /work/rtl/kernellum_local_mac_array.sv \
    /work/rtl/similarity_asic_transfer_top.sv

export SDC_FILE = /work/asic/transfer/constraints.sdc
export CORE_UTILIZATION = 35
export PLACE_DENSITY = 0.50
export TNS_END_PERCENT = 100
export LEC_CHECK = 0
export SKIP_CTS_REPAIR_TIMING = 1
