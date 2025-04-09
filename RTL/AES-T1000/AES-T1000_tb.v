`timescale 1ns/1ps
module AES_T1000_tb();
reg clk;
reg rst;
reg [127:0] state;
reg [127:0] key;
wire [63:0] Capacitance;

// 实例化待测模块
top uut (
    .clk(clk),
    .rst(rst),
    .state(state),
    .key(key),
    .Capacitance(Capacitance)
    );

// 时钟激励
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// 复位激励
initial begin
    rst = 1;
    #10;
    rst = 0;
end

integer i;
initial begin
    state = 0;
    key = 0;
    #10;
    for(i = 0; i < 400; i = i + 1) begin
        $display("********Period %d********", i);
        state = $random;
        key = $random;
        if(i == 200) state = 128'h00112233_44556677_8899aabb_ccddeeff;
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, AES_T1000_tb);
end

endmodule
