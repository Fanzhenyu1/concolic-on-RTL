`timescale 1ns/1ps
module case_aes_tb();
reg clk;
reg rst;
reg [127:0] state;
reg [127:0] key;
wire [127:0] out;
wire [63:0] Capacitance;

// 实例化待测模块
case_aes uut (
    .clk(clk),
    .rst(rst),
    .state(state),
    .key(key),
    .out(out),
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
    for(i = 0; i < 100; i = i + 1) begin
        $display("********Period %d********", i);
        state = $random;
        key = $random;

        if(i == 50) state = 128'h3243f6a8_885a308d_313198a2_e0370734;
        if(i == 51) state = 128'h00112233_44556677_8899aabb_ccddeeff;
        if(i == 52) state = 128'h0;
        if(i == 53) state = 128'h1;


        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, case_aes_tb);
end

endmodule
