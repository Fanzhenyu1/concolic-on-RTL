//~ `New testbench
`timescale  1ns / 1ps

module tb_uart_top;

// uart_top Parameters
parameter PERIOD  = 10;


// uart_top Inputs
reg   sys_clk                              = 0 ;
reg   sys_rst_l                            = 0 ;
reg   xmitH                                = 0 ;
reg   [7:0]  xmit_dataH                    = 0 ;
reg   uart_REC_dataH                       = 0 ;

// uart_top Outputs
wire  uart_XMIT_dataH                      ;
wire  xmit_doneH                           ;
wire  [7:0]  rec_dataH                     ;
wire  rec_readyH                           ;


initial
begin
    forever #(PERIOD/2)  sys_clk=~sys_clk;
end

initial
begin
    #(PERIOD*2) sys_rst_l  =  1;
end

uart_top  u_uart_top (
    .sys_clk                 ( sys_clk                ),
    .sys_rst_l               ( sys_rst_l              ),
    .xmitH                   ( xmitH                  ),
    .xmit_dataH              ( xmit_dataH       [7:0] ),
    .uart_REC_dataH          ( uart_REC_dataH         ),

    .uart_XMIT_dataH         ( uart_XMIT_dataH        ),
    .xmit_doneH              ( xmit_doneH             ),
    .rec_dataH               ( rec_dataH        [7:0] ),
    .rec_readyH              ( rec_readyH             )
);

integer i;
initial begin

    xmitH = 0;
    xmit_dataH = 0;
    uart_REC_dataH = 0;
    #10;
    for(i = 0; i < 100; i = i + 1) begin
        #8;

        xmitH = $random & 1'd1;
        xmit_dataH = $random & 8'd255;
        uart_REC_dataH = $random & 1'd1;
        #2;
    end

    $finish;
end

initial
begin            
    $dumpfile("wave.vcd");        //生成的vcd文件名称
    $dumpvars(0, tb_uart_top);    //tb模块名称
end 
endmodule