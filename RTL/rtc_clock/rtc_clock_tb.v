//~ `New testbench
`timescale  1ns / 1ps

module tb_rtc_clock;

// rtc_clock Parameters
parameter PERIOD  = 10;


// rtc_clock Inputs
reg           clk_i                   = 0 ;
reg           rstn_i                  = 0 ;
reg           clock_update_i          = 0 ;
reg    [21:0] clock_i                 = 0 ;
reg    [14:0] init_sec_cnt_i          = 0 ;

// rtc_clock Outputs
wire   [21:0] clock_o                 ;
wire          update_day_o            ;


initial
begin
    forever #(PERIOD/2)  clk_i=~clk_i;
end

initial
begin
    #(PERIOD*2) rstn_i  =  1;
end

rtc_clock  u_rtc_clock (
    .        clk_i           (         clk_i            ),
    .        rstn_i          (         rstn_i           ),
    .        clock_update_i  (         clock_update_i   ),
    . clock_i         (  clock_i          ),
    . init_sec_cnt_i  (  init_sec_cnt_i   ),

    . clock_o         (  clock_o          ),
    .        update_day_o    (         update_day_o     )
);

initial
begin
    # (PERIOD*2);
    clock_i = 22'h235859;
    init_sec_cnt_i = 15'h7ffe;
    clock_update_i = 1;
    # PERIOD clock_update_i = 0;
    # (PERIOD*4);

    clock_i = 22'h225959;
    init_sec_cnt_i = 15'h7ffe;
    clock_update_i = 1;
    # PERIOD clock_update_i = 0;
    # (PERIOD*4);

    clock_i = 22'h235959;
    init_sec_cnt_i = 15'h7ffe;
    clock_update_i = 1;
    # PERIOD clock_update_i = 0;
    # (PERIOD*4);

    $finish;
end

initial
begin            
    $dumpfile("wave.vcd");        //生成的vcd文件名称
    $dumpvars(0, tb_rtc_clock);    //tb模块名称
end 

endmodule