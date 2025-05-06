`timescale 1ns/1ps
module b14_tb();
reg clock;
reg reset;
reg [30:0] datai;
wire [19:0] addr;
wire [30:0] datao;
wire rd;
wire wr;

// 实例化待测模块
b14 uut (
    .clock(clock),
    .reset(reset),
    .datai(datai),
    .addr(addr),
    .datao(datao),
    .rd(rd),
    .wr(wr)
    );

// 时钟激励
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// 复位激励
initial begin
    reset = 1;
    #10;
    reset = 0;
end

integer i;
initial begin
    clock = 0;
    datai = 0;
    #10;
    for(i = 0; i < 100; i = i + 1) begin
        $display("********Period %d********", i);
        clock = $random & 1'd1;
        datai = $random & 31'd2147483647;
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, b14_tb);
end

endmodule
