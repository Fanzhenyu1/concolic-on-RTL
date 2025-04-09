`timescale 1ns/1ps
module adbg_tap_top_tb();
reg tms_pad_i;
reg tck_pad_i;
reg trstn_pad_i;
reg tdi_pad_i;
wire tdo_pad_o;
wire tdo_padoe_o;
reg test_mode_i;
wire test_logic_reset_o;
wire run_test_idle_o;
wire shift_dr_o;
wire pause_dr_o;
wire update_dr_o;
wire capture_dr_o;
wire extest_select_o;
wire sample_preload_select_o;
wire mbist_select_o;
wire debug_select_o;
wire tdi_o;
reg debug_tdo_i;
reg bs_chain_tdo_i;
reg mbist_tdo_i;

// 实例化待测模块
adbg_tap_top uut (
    .tms_pad_i(tms_pad_i),
    .tck_pad_i(tck_pad_i),
    .trstn_pad_i(trstn_pad_i),
    .tdi_pad_i(tdi_pad_i),
    .tdo_pad_o(tdo_pad_o),
    .tdo_padoe_o(tdo_padoe_o),
    .test_mode_i(test_mode_i),
    .test_logic_reset_o(test_logic_reset_o),
    .run_test_idle_o(run_test_idle_o),
    .shift_dr_o(shift_dr_o),
    .pause_dr_o(pause_dr_o),
    .update_dr_o(update_dr_o),
    .capture_dr_o(capture_dr_o),
    .extest_select_o(extest_select_o),
    .sample_preload_select_o(sample_preload_select_o),
    .mbist_select_o(mbist_select_o),
    .debug_select_o(debug_select_o),
    .tdi_o(tdi_o),
    .debug_tdo_i(debug_tdo_i),
    .bs_chain_tdo_i(bs_chain_tdo_i),
    .mbist_tdo_i(mbist_tdo_i)
    );

// 时钟激励
initial begin
    tck_pad_i = 0;
    forever #5 tck_pad_i = ~tck_pad_i;
end

// 复位激励
initial begin
    trstn_pad_i = 0;
    #10;
    trstn_pad_i = 1;
end

integer i;
initial begin
    tms_pad_i = 1;
    tdi_pad_i = 0;
    test_mode_i = 0;
    debug_tdo_i = 0;
    bs_chain_tdo_i = 0;
    mbist_tdo_i = 0;
    #10;
    for(i = 0; i < 400; i = i + 1) begin
        $display("********Period %d********", i);
        tms_pad_i = $random & 1'd1;
        tdi_pad_i = $random & 1'd1;
        test_mode_i = $random & 1'd1;
        debug_tdo_i = $random & 1'd1;
        bs_chain_tdo_i = $random & 1'd1;
        mbist_tdo_i = $random & 1'd1;
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, adbg_tap_top_tb);
end

endmodule
