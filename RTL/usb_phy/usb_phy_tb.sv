//~ `New testbench
`timescale  1ns / 1ps

module tb_usb_phy;

// usb_phy Parameters
parameter PERIOD  = 10;


// usb_phy Inputs
reg   clk                                  = 0 ;
reg   rst                                  = 0 ;
reg   phy_tx_mode                          = 0 ;
reg   rxd                                  = 0 ;
reg   rxdp                                 = 0 ;
reg   rxdn                                 = 0 ;
reg   [7:0]  DataOut_i                     = 0 ;
reg   TxValid_i                            = 0 ;

// usb_phy Outputs
wire  usb_rst                              ;
wire  txdp                                 ;
wire  txdn                                 ;
wire  txoe                                 ;
wire  TxReady_o                            ;
wire  RxValid_o                            ;
wire  RxActive_o                           ;
wire  RxError_o                            ;
wire  [7:0]  DataIn_o                      ;
wire  [1:0]  LineState_o                   ;


initial
begin
    forever #(PERIOD/2)  clk=~clk;
end

initial
begin
    #(PERIOD) rst  =  1;
end

usb_phy  u_usb_phy (
    .clk                     ( clk                ),
    .rst                     ( rst                ),
    .phy_tx_mode             ( phy_tx_mode        ),
    .rxd                     ( rxd                ),
    .rxdp                    ( rxdp               ),
    .rxdn                    ( rxdn               ),
    .DataOut_i               ( DataOut_i    [7:0] ),
    .TxValid_i               ( TxValid_i          ),

    .usb_rst                 ( usb_rst            ),
    .txdp                    ( txdp               ),
    .txdn                    ( txdn               ),
    .txoe                    ( txoe               ),
    .TxReady_o               ( TxReady_o          ),
    .RxValid_o               ( RxValid_o          ),
    .RxActive_o              ( RxActive_o         ),
    .RxError_o               ( RxError_o          ),
    .DataIn_o                ( DataIn_o     [7:0] ),
    .LineState_o             ( LineState_o  [1:0] )
);

integer seed;
initial begin
    // 获取命令行参数中的SEED，若无则用默认值

    if ($value$plusargs("SEED=%d", seed)) begin
        $display("[INFO] Using SEED from command line: %0d", seed);
        $urandom(seed);  // 初始化SystemVerilog随机生成器
    end
end

integer i;
initial begin
    clk = 0;
    rst = 0;
    phy_tx_mode = 0;
    rxd = 0;
    rxdp = 0;
    rxdn = 0;
    DataOut_i = 0;
    TxValid_i = 0;
    #10;
    for(i = 0; i < 8000; i = i + 1) begin
        $display("********Period %d********", i);
        phy_tx_mode = $urandom & 1'd1;
        rxd = $urandom & 1'd1;
        rxdp = $urandom & 1'd1;
        rxdn = $urandom & 1'd1;
        DataOut_i = $urandom & 8'd255;
        TxValid_i = $urandom & 1'd1;
        if(i == 6368) begin rxd = 0; end
        if(i == 6369) begin rxd = 0; end
        if(i == 6371)
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, tb_usb_phy);
end

endmodule