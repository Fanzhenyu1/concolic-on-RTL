`timescale 1ns/1ps
module b11_tb();
reg [5:0] x_in;
reg stbi;
reg clock;
reg reset;
wire [5:0] x_out;

// 实例化待测模块
b11 uut (
    .x_in(x_in),
    .stbi(stbi),
    .clock(clock),
    .reset(reset),
    .x_out(x_out)
    );

// 时钟激励
initial begin
    clock = 0;
    forever #5 clock = ~clock;
end

// 复位激励
initial begin
    reset = 1;
    #10;
    reset = 0;
end
 
integer i;
initial begin
    x_in = 0;
    stbi = 0;
    #10;
    for(i = 0; i < 100; i = i + 1) begin
        $display("********Period %d********", i);
        x_in = $random & 6'd63;
        stbi = $random & 1'd1;
        if(i == 3) begin x_in = 6'b0; stbi = 0; end
        if(i == 8) begin x_in[3:2] = 2'b11; end
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, b11_tb);
end

endmodule
