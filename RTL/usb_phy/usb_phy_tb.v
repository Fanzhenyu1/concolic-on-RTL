`timescale 1ns/1ps
module usb_phy_tb();
reg clk;
reg rst;
reg phy_tx_mode;
wire usb_rst;
wire txdp;
wire txdn;
wire txoe;
reg rxd;
reg rxdp;
reg rxdn;
reg [7:0] DataOut_i;
reg TxValid_i;
wire TxReady_o;
wire RxValid_o;
wire RxActive_o;
wire RxError_o;
wire [7:0] DataIn_o;
wire [1:0] LineState_o;

// 实例化待测模块
usb_phy uut (
    .clk(clk),
    .rst(rst),
    .phy_tx_mode(phy_tx_mode),
    .usb_rst(usb_rst),
    .txdp(txdp),
    .txdn(txdn),
    .txoe(txoe),
    .rxd(rxd),
    .rxdp(rxdp),
    .rxdn(rxdn),
    .DataOut_i(DataOut_i),
    .TxValid_i(TxValid_i),
    .TxReady_o(TxReady_o),
    .RxValid_o(RxValid_o),
    .RxActive_o(RxActive_o),
    .RxError_o(RxError_o),
    .DataIn_o(DataIn_o),
    .LineState_o(LineState_o)
    );

// 时钟激励
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// 复位激励
initial begin
    rst = 0;
    #10;
    rst = 1;
end

integer i;
initial begin
    phy_tx_mode = 0;
    rxd = 0;
    rxdp = 0;
    rxdn = 0;
    DataOut_i = 0;
    TxValid_i = 0;
    #10;
    for(i = 0; i < 4000; i = i + 1) begin
        $display("********Period %d********", i);
        phy_tx_mode = $random & 1'd1;
        rxd = $random & 1'd1;
        rxdp = $random & 1'd1;
        rxdn = $random & 1'd1;
        DataOut_i = $random & 8'd255;
        TxValid_i = $random & 1'd1;
        // if(i == 2301) begin rxdn = 1'b0; end
        // if(i == 2302) begin rxdp = 1'b0; rxdn = 1'b1; end
        // if(i == 2303) begin rxdp = 1'b0; rxdn = 1'b1; end
        // if(i == 2304) begin rxdp = 1'b0; rxdn = 1'b0; end
        // if(i >= 2295 && i < 2315) TxValid_i = 1'b0;
        // if(i == 2308) begin rxdn = 1'b0; end
        // if(i == 2309) begin rxdp = 1'b0; rxdn = 1'b1; end
        // if(i == 2310) begin rxdp = 1'b0; rxdn = 1'b1; end
        // if(i == 2311) begin rxdp = 1'b0; rxdn = 1'b0; end

        // if(i == 2316) begin rxdn = 1'b0; end
        // if(i == 2317) begin rxdp = 1'b0; rxdn = 1'b1; end
        // if(i == 2318) begin rxdp = 1'b0; rxdn = 1'b1; end
        // if(i == 2319) begin rxdp = 1'b0; rxdn = 1'b0; end
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, usb_phy_tb);
end

endmodule
