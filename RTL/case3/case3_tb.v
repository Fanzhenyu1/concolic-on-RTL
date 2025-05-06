`timescale 1ns/1ps
module case3_tb();
reg _a;
reg _b;
reg clk;
reg rst;
reg [31:0] input_a;
reg [31:0] input_b;
reg [31:0] ctr;
wire [31:0] ht_out;

// 实例化待测模块
case3 uut (
    .clk(clk),
    .rst(rst),
    .input_a(input_a),
    .input_b(input_b),
    .ctr(ctr),
    .ht_out(ht_out)
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
    input_a = 0;
    input_b = 0;
    ctr = 0;
    #10;
    for(i = 0; i < 16; i = i + 1) begin
        $display("********Period %d********", i);
        input_a = $random;
        input_b = $random;
        ctr = $random;
        // if(i == 1) ctr = 32'd305419896;
        #10;
    end
// Cycle 0
    input_a = 32'd287454020;
    input_b = $random;
    ctr = $random;
    #10;

// Cycle 1
    input_a = 32'd2578103244;
    input_b = 32'd3721195263;
    ctr = 32'd305419896;
    #10;

// Cycle 2
    input_a = $random;
    input_b = 32'd1432778632;
    ctr = $random;
    #10;

// Cycle 3
    input_a = $random;
    input_b = $random;
    ctr = $random;
    #10;
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, case3_tb);
end

endmodule
