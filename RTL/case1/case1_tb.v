`timescale 1ns/1ps
module case1_tb();
reg [7:0] in;
wire [7:0] out;
reg clk;
reg rst;

// 实例化待测模块
case1 uut (
    .in(in),
    .out(out),
    .clk(clk),
    .rst(rst)
    );

// 时钟激励
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// 复位激励
initial begin
    rst = 1;
    #20;
    rst = 0;
end

integer i;
initial begin
    in = 0;
    #10;
    for(i = 0; i < 100; i = i + 1) begin
        $display("********Period %d********", i);
        in = $random & 8'd255;
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, case1_tb);
end

endmodule
