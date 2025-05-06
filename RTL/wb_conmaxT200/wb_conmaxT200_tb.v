`timescale 1ns/1ps
module wb_conmaxT200_tb();
reg clk_i;
reg rst_i;
reg [31:0] m0_addr_i;
reg [31:0] s0_data_i;
reg [31:0] s1_data_i;
reg [31:0] s2_data_i;
reg [31:0] s3_data_i;
reg [31:0] s4_data_i;
reg [31:0] s5_data_i;
reg [31:0] s6_data_i;
reg [31:0] s7_data_i;
reg [31:0] s8_data_i;
reg [31:0] s9_data_i;
reg [31:0] s10_data_i;
reg [31:0] s11_data_i;
reg [31:0] s12_data_i;
reg [31:0] s13_data_i;
reg [31:0] s14_data_i;
reg [31:0] s15_data_i;
wire trigger;

// 实例化待测模块
wb_conmaxT200 uut (
    .clk_i(clk_i),
    .rst_i(rst_i),
    .m0_addr_i(m0_addr_i),
    .s0_data_i(s0_data_i),
    .s1_data_i(s1_data_i),
    .s2_data_i(s2_data_i),
    .s3_data_i(s3_data_i),
    .s4_data_i(s4_data_i),
    .s5_data_i(s5_data_i),
    .s6_data_i(s6_data_i),
    .s7_data_i(s7_data_i),
    .s8_data_i(s8_data_i),
    .s9_data_i(s9_data_i),
    .s10_data_i(s10_data_i),
    .s11_data_i(s11_data_i),
    .s12_data_i(s12_data_i),
    .s13_data_i(s13_data_i),
    .s14_data_i(s14_data_i),
    .s15_data_i(s15_data_i),
    .trigger(trigger)
    );

// 时钟激励
initial begin
    clk_i = 0;
    forever #5 clk_i = ~clk_i;
end

// 复位激励
initial begin
    rst_i = 1;
    #10;
    rst_i = 0;
end

integer i;
initial begin
    m0_addr_i = 0;
    s0_data_i = 0;
    s1_data_i = 0;
    s2_data_i = 0;
    s3_data_i = 0;
    s4_data_i = 0;
    s5_data_i = 0;
    s6_data_i = 0;
    s7_data_i = 0;
    s8_data_i = 0;
    s9_data_i = 0;
    s10_data_i = 0;
    s11_data_i = 0;
    s12_data_i = 0;
    s13_data_i = 0;
    s14_data_i = 0;
    s15_data_i = 0;
    #10;
    for(i = 0; i < 100; i = i + 1) begin
        $display("********Period %d********", i);
        m0_addr_i = $random;
        s0_data_i = $random;
        s1_data_i = $random;
        s2_data_i = $random;
        s3_data_i = $random;
        s4_data_i = $random;
        s5_data_i = $random;
        s6_data_i = $random;
        s7_data_i = $random;
        s8_data_i = $random;
        s9_data_i = $random;
        s10_data_i = $random;
        s11_data_i = $random;
        s12_data_i = $random;
        s13_data_i = $random;
        s14_data_i = $random;
        s15_data_i = $random;

        if(i == 10) begin m0_addr_i[31:28] = 4'b0000; s0_data_i = 32'h00000000; end
        if(i == 11) begin m0_addr_i[31:28] = 4'b0000; s0_data_i = 32'h3553B86C; end
        if(i == 12) begin m0_addr_i[31:28] = 4'b0000; s0_data_i = 32'hEAAAD8FF; end
        if(i == 13) begin m0_addr_i[31:28] = 4'b0000; s0_data_i = 32'hAA970B8; end

        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, wb_conmaxT200_tb);
end

endmodule
