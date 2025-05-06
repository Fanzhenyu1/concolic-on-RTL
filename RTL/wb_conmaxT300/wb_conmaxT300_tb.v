`timescale 1ns/1ps
module wb_conmaxT300_tb();
reg clk_i;
reg rst_i;
reg [31:0] wb_data_i;
wire [31:0] wb_data_o;
reg [31:0] wb_addr_i;
reg [3:0] wb_sel_i;
reg wb_we_i;
reg wb_cyc_i;
reg wb_stb_i;
wire wb_ack_o;
wire wb_err_o;
wire wb_rty_o;
reg [31:0] s0_data_i;
wire [31:0] s0_data_o;
wire [31:0] s0_addr_o;
wire [3:0] s0_sel_o;
wire s0_we_o;
wire s0_cyc_o;
wire s0_stb_o;
reg s0_ack_i;
reg s0_err_i;
reg s0_rty_i;
reg [31:0] s1_data_i;
wire [31:0] s1_data_o;
wire [31:0] s1_addr_o;
wire [3:0] s1_sel_o;
wire s1_we_o;
wire s1_cyc_o;
wire s1_stb_o;
reg s1_ack_i;
reg s1_err_i;
reg s1_rty_i;
reg [31:0] s2_data_i;
wire [31:0] s2_data_o;
wire [31:0] s2_addr_o;
wire [3:0] s2_sel_o;
wire s2_we_o;
wire s2_cyc_o;
wire s2_stb_o;
reg s2_ack_i;
reg s2_err_i;
reg s2_rty_i;
reg [31:0] s3_data_i;
wire [31:0] s3_data_o;
wire [31:0] s3_addr_o;
wire [3:0] s3_sel_o;
wire s3_we_o;
wire s3_cyc_o;
wire s3_stb_o;
reg s3_ack_i;
reg s3_err_i;
reg s3_rty_i;
reg [31:0] s4_data_i;
wire [31:0] s4_data_o;
wire [31:0] s4_addr_o;
wire [3:0] s4_sel_o;
wire s4_we_o;
wire s4_cyc_o;
wire s4_stb_o;
reg s4_ack_i;
reg s4_err_i;
reg s4_rty_i;
reg [31:0] s5_data_i;
wire [31:0] s5_data_o;
wire [31:0] s5_addr_o;
wire [3:0] s5_sel_o;
wire s5_we_o;
wire s5_cyc_o;
wire s5_stb_o;
reg s5_ack_i;
reg s5_err_i;
reg s5_rty_i;
reg [31:0] s6_data_i;
wire [31:0] s6_data_o;
wire [31:0] s6_addr_o;
wire [3:0] s6_sel_o;
wire s6_we_o;
wire s6_cyc_o;
wire s6_stb_o;
reg s6_ack_i;
reg s6_err_i;
reg s6_rty_i;
reg [31:0] s7_data_i;
wire [31:0] s7_data_o;
wire [31:0] s7_addr_o;
wire [3:0] s7_sel_o;
wire s7_we_o;
wire s7_cyc_o;
wire s7_stb_o;
reg s7_ack_i;
reg s7_err_i;
reg s7_rty_i;
reg [31:0] s8_data_i;
wire [31:0] s8_data_o;
wire [31:0] s8_addr_o;
wire [3:0] s8_sel_o;
wire s8_we_o;
wire s8_cyc_o;
wire s8_stb_o;
reg s8_ack_i;
reg s8_err_i;
reg s8_rty_i;
reg [31:0] s9_data_i;
wire [31:0] s9_data_o;
wire [31:0] s9_addr_o;
wire [3:0] s9_sel_o;
wire s9_we_o;
wire s9_cyc_o;
wire s9_stb_o;
reg s9_ack_i;
reg s9_err_i;
reg s9_rty_i;
reg [31:0] s10_data_i;
wire [31:0] s10_data_o;
wire [31:0] s10_addr_o;
wire [3:0] s10_sel_o;
wire s10_we_o;
wire s10_cyc_o;
wire s10_stb_o;
reg s10_ack_i;
reg s10_err_i;
reg s10_rty_i;
reg [31:0] s11_data_i;
wire [31:0] s11_data_o;
wire [31:0] s11_addr_o;
wire [3:0] s11_sel_o;
wire s11_we_o;
wire s11_cyc_o;
wire s11_stb_o;
reg s11_ack_i;
reg s11_err_i;
reg s11_rty_i;
reg [31:0] s12_data_i;
wire [31:0] s12_data_o;
wire [31:0] s12_addr_o;
wire [3:0] s12_sel_o;
wire s12_we_o;
wire s12_cyc_o;
wire s12_stb_o;
reg s12_ack_i;
reg s12_err_i;
reg s12_rty_i;
reg [31:0] s13_data_i;
wire [31:0] s13_data_o;
wire [31:0] s13_addr_o;
wire [3:0] s13_sel_o;
wire s13_we_o;
wire s13_cyc_o;
wire s13_stb_o;
reg s13_ack_i;
reg s13_err_i;
reg s13_rty_i;
reg [31:0] s14_data_i;
wire [31:0] s14_data_o;
wire [31:0] s14_addr_o;
wire [3:0] s14_sel_o;
wire s14_we_o;
wire s14_cyc_o;
wire s14_stb_o;
reg s14_ack_i;
reg s14_err_i;
reg s14_rty_i;
reg [31:0] s15_data_i;
wire [31:0] s15_data_o;
wire [31:0] s15_addr_o;
wire [3:0] s15_sel_o;
wire s15_we_o;
wire s15_cyc_o;
wire s15_stb_o;
reg s15_ack_i;
reg s15_err_i;
reg s15_rty_i;

// 实例化待测模块
wb_conmaxT300 uut (
    .clk_i(clk_i),
    .rst_i(rst_i),
    .wb_data_i(wb_data_i),
    .wb_data_o(wb_data_o),
    .wb_addr_i(wb_addr_i),
    .wb_sel_i(wb_sel_i),
    .wb_we_i(wb_we_i),
    .wb_cyc_i(wb_cyc_i),
    .wb_stb_i(wb_stb_i),
    .wb_ack_o(wb_ack_o),
    .wb_err_o(wb_err_o),
    .wb_rty_o(wb_rty_o),
    .s0_data_i(s0_data_i),
    .s0_data_o(s0_data_o),
    .s0_addr_o(s0_addr_o),
    .s0_sel_o(s0_sel_o),
    .s0_we_o(s0_we_o),
    .s0_cyc_o(s0_cyc_o),
    .s0_stb_o(s0_stb_o),
    .s0_ack_i(s0_ack_i),
    .s0_err_i(s0_err_i),
    .s0_rty_i(s0_rty_i),
    .s1_data_i(s1_data_i),
    .s1_data_o(s1_data_o),
    .s1_addr_o(s1_addr_o),
    .s1_sel_o(s1_sel_o),
    .s1_we_o(s1_we_o),
    .s1_cyc_o(s1_cyc_o),
    .s1_stb_o(s1_stb_o),
    .s1_ack_i(s1_ack_i),
    .s1_err_i(s1_err_i),
    .s1_rty_i(s1_rty_i),
    .s2_data_i(s2_data_i),
    .s2_data_o(s2_data_o),
    .s2_addr_o(s2_addr_o),
    .s2_sel_o(s2_sel_o),
    .s2_we_o(s2_we_o),
    .s2_cyc_o(s2_cyc_o),
    .s2_stb_o(s2_stb_o),
    .s2_ack_i(s2_ack_i),
    .s2_err_i(s2_err_i),
    .s2_rty_i(s2_rty_i),
    .s3_data_i(s3_data_i),
    .s3_data_o(s3_data_o),
    .s3_addr_o(s3_addr_o),
    .s3_sel_o(s3_sel_o),
    .s3_we_o(s3_we_o),
    .s3_cyc_o(s3_cyc_o),
    .s3_stb_o(s3_stb_o),
    .s3_ack_i(s3_ack_i),
    .s3_err_i(s3_err_i),
    .s3_rty_i(s3_rty_i),
    .s4_data_i(s4_data_i),
    .s4_data_o(s4_data_o),
    .s4_addr_o(s4_addr_o),
    .s4_sel_o(s4_sel_o),
    .s4_we_o(s4_we_o),
    .s4_cyc_o(s4_cyc_o),
    .s4_stb_o(s4_stb_o),
    .s4_ack_i(s4_ack_i),
    .s4_err_i(s4_err_i),
    .s4_rty_i(s4_rty_i),
    .s5_data_i(s5_data_i),
    .s5_data_o(s5_data_o),
    .s5_addr_o(s5_addr_o),
    .s5_sel_o(s5_sel_o),
    .s5_we_o(s5_we_o),
    .s5_cyc_o(s5_cyc_o),
    .s5_stb_o(s5_stb_o),
    .s5_ack_i(s5_ack_i),
    .s5_err_i(s5_err_i),
    .s5_rty_i(s5_rty_i),
    .s6_data_i(s6_data_i),
    .s6_data_o(s6_data_o),
    .s6_addr_o(s6_addr_o),
    .s6_sel_o(s6_sel_o),
    .s6_we_o(s6_we_o),
    .s6_cyc_o(s6_cyc_o),
    .s6_stb_o(s6_stb_o),
    .s6_ack_i(s6_ack_i),
    .s6_err_i(s6_err_i),
    .s6_rty_i(s6_rty_i),
    .s7_data_i(s7_data_i),
    .s7_data_o(s7_data_o),
    .s7_addr_o(s7_addr_o),
    .s7_sel_o(s7_sel_o),
    .s7_we_o(s7_we_o),
    .s7_cyc_o(s7_cyc_o),
    .s7_stb_o(s7_stb_o),
    .s7_ack_i(s7_ack_i),
    .s7_err_i(s7_err_i),
    .s7_rty_i(s7_rty_i),
    .s8_data_i(s8_data_i),
    .s8_data_o(s8_data_o),
    .s8_addr_o(s8_addr_o),
    .s8_sel_o(s8_sel_o),
    .s8_we_o(s8_we_o),
    .s8_cyc_o(s8_cyc_o),
    .s8_stb_o(s8_stb_o),
    .s8_ack_i(s8_ack_i),
    .s8_err_i(s8_err_i),
    .s8_rty_i(s8_rty_i),
    .s9_data_i(s9_data_i),
    .s9_data_o(s9_data_o),
    .s9_addr_o(s9_addr_o),
    .s9_sel_o(s9_sel_o),
    .s9_we_o(s9_we_o),
    .s9_cyc_o(s9_cyc_o),
    .s9_stb_o(s9_stb_o),
    .s9_ack_i(s9_ack_i),
    .s9_err_i(s9_err_i),
    .s9_rty_i(s9_rty_i),
    .s10_data_i(s10_data_i),
    .s10_data_o(s10_data_o),
    .s10_addr_o(s10_addr_o),
    .s10_sel_o(s10_sel_o),
    .s10_we_o(s10_we_o),
    .s10_cyc_o(s10_cyc_o),
    .s10_stb_o(s10_stb_o),
    .s10_ack_i(s10_ack_i),
    .s10_err_i(s10_err_i),
    .s10_rty_i(s10_rty_i),
    .s11_data_i(s11_data_i),
    .s11_data_o(s11_data_o),
    .s11_addr_o(s11_addr_o),
    .s11_sel_o(s11_sel_o),
    .s11_we_o(s11_we_o),
    .s11_cyc_o(s11_cyc_o),
    .s11_stb_o(s11_stb_o),
    .s11_ack_i(s11_ack_i),
    .s11_err_i(s11_err_i),
    .s11_rty_i(s11_rty_i),
    .s12_data_i(s12_data_i),
    .s12_data_o(s12_data_o),
    .s12_addr_o(s12_addr_o),
    .s12_sel_o(s12_sel_o),
    .s12_we_o(s12_we_o),
    .s12_cyc_o(s12_cyc_o),
    .s12_stb_o(s12_stb_o),
    .s12_ack_i(s12_ack_i),
    .s12_err_i(s12_err_i),
    .s12_rty_i(s12_rty_i),
    .s13_data_i(s13_data_i),
    .s13_data_o(s13_data_o),
    .s13_addr_o(s13_addr_o),
    .s13_sel_o(s13_sel_o),
    .s13_we_o(s13_we_o),
    .s13_cyc_o(s13_cyc_o),
    .s13_stb_o(s13_stb_o),
    .s13_ack_i(s13_ack_i),
    .s13_err_i(s13_err_i),
    .s13_rty_i(s13_rty_i),
    .s14_data_i(s14_data_i),
    .s14_data_o(s14_data_o),
    .s14_addr_o(s14_addr_o),
    .s14_sel_o(s14_sel_o),
    .s14_we_o(s14_we_o),
    .s14_cyc_o(s14_cyc_o),
    .s14_stb_o(s14_stb_o),
    .s14_ack_i(s14_ack_i),
    .s14_err_i(s14_err_i),
    .s14_rty_i(s14_rty_i),
    .s15_data_i(s15_data_i),
    .s15_data_o(s15_data_o),
    .s15_addr_o(s15_addr_o),
    .s15_sel_o(s15_sel_o),
    .s15_we_o(s15_we_o),
    .s15_cyc_o(s15_cyc_o),
    .s15_stb_o(s15_stb_o),
    .s15_ack_i(s15_ack_i),
    .s15_err_i(s15_err_i),
    .s15_rty_i(s15_rty_i)
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
    wb_data_i = 0;
    wb_addr_i = 0;
    wb_sel_i = 0;
    wb_we_i = 0;
    wb_cyc_i = 0;
    wb_stb_i = 0;
    s0_data_i = 0;
    s0_ack_i = 0;
    s0_err_i = 0;
    s0_rty_i = 0;
    s1_data_i = 0;
    s1_ack_i = 0;
    s1_err_i = 0;
    s1_rty_i = 0;
    s2_data_i = 0;
    s2_ack_i = 0;
    s2_err_i = 0;
    s2_rty_i = 0;
    s3_data_i = 0;
    s3_ack_i = 0;
    s3_err_i = 0;
    s3_rty_i = 0;
    s4_data_i = 0;
    s4_ack_i = 0;
    s4_err_i = 0;
    s4_rty_i = 0;
    s5_data_i = 0;
    s5_ack_i = 0;
    s5_err_i = 0;
    s5_rty_i = 0;
    s6_data_i = 0;
    s6_ack_i = 0;
    s6_err_i = 0;
    s6_rty_i = 0;
    s7_data_i = 0;
    s7_ack_i = 0;
    s7_err_i = 0;
    s7_rty_i = 0;
    s8_data_i = 0;
    s8_ack_i = 0;
    s8_err_i = 0;
    s8_rty_i = 0;
    s9_data_i = 0;
    s9_ack_i = 0;
    s9_err_i = 0;
    s9_rty_i = 0;
    s10_data_i = 0;
    s10_ack_i = 0;
    s10_err_i = 0;
    s10_rty_i = 0;
    s11_data_i = 0;
    s11_ack_i = 0;
    s11_err_i = 0;
    s11_rty_i = 0;
    s12_data_i = 0;
    s12_ack_i = 0;
    s12_err_i = 0;
    s12_rty_i = 0;
    s13_data_i = 0;
    s13_ack_i = 0;
    s13_err_i = 0;
    s13_rty_i = 0;
    s14_data_i = 0;
    s14_ack_i = 0;
    s14_err_i = 0;
    s14_rty_i = 0;
    s15_data_i = 0;
    s15_ack_i = 0;
    s15_err_i = 0;
    s15_rty_i = 0;
    #10;
    for(i = 0; i < 100; i = i + 1) begin
        $display("********Period %d********", i);
        wb_data_i = $random;
        wb_addr_i = $random;
        wb_sel_i = $random & 4'd15;
        wb_we_i = $random & 1'd1;
        wb_cyc_i = $random & 1'd1;
        wb_stb_i = $random & 1'd1;
        s0_data_i = $random;
        s0_ack_i = $random & 1'd1;
        s0_err_i = $random & 1'd1;
        s0_rty_i = $random & 1'd1;
        s1_data_i = $random;
        s1_ack_i = $random & 1'd1;
        s1_err_i = $random & 1'd1;
        s1_rty_i = $random & 1'd1;
        s2_data_i = $random;
        s2_ack_i = $random & 1'd1;
        s2_err_i = $random & 1'd1;
        s2_rty_i = $random & 1'd1;
        s3_data_i = $random;
        s3_ack_i = $random & 1'd1;
        s3_err_i = $random & 1'd1;
        s3_rty_i = $random & 1'd1;
        s4_data_i = $random;
        s4_ack_i = $random & 1'd1;
        s4_err_i = $random & 1'd1;
        s4_rty_i = $random & 1'd1;
        s5_data_i = $random;
        s5_ack_i = $random & 1'd1;
        s5_err_i = $random & 1'd1;
        s5_rty_i = $random & 1'd1;
        s6_data_i = $random;
        s6_ack_i = $random & 1'd1;
        s6_err_i = $random & 1'd1;
        s6_rty_i = $random & 1'd1;
        s7_data_i = $random;
        s7_ack_i = $random & 1'd1;
        s7_err_i = $random & 1'd1;
        s7_rty_i = $random & 1'd1;
        s8_data_i = $random;
        s8_ack_i = $random & 1'd1;
        s8_err_i = $random & 1'd1;
        s8_rty_i = $random & 1'd1;
        s9_data_i = $random;
        s9_ack_i = $random & 1'd1;
        s9_err_i = $random & 1'd1;
        s9_rty_i = $random & 1'd1;
        s10_data_i = $random;
        s10_ack_i = $random & 1'd1;
        s10_err_i = $random & 1'd1;
        s10_rty_i = $random & 1'd1;
        s11_data_i = $random;
        s11_ack_i = $random & 1'd1;
        s11_err_i = $random & 1'd1;
        s11_rty_i = $random & 1'd1;
        s12_data_i = $random;
        s12_ack_i = $random & 1'd1;
        s12_err_i = $random & 1'd1;
        s12_rty_i = $random & 1'd1;
        s13_data_i = $random;
        s13_ack_i = $random & 1'd1;
        s13_err_i = $random & 1'd1;
        s13_rty_i = $random & 1'd1;
        s14_data_i = $random;
        s14_ack_i = $random & 1'd1;
        s14_err_i = $random & 1'd1;
        s14_rty_i = $random & 1'd1;
        s15_data_i = $random;
        s15_ack_i = $random & 1'd1;
        s15_err_i = $random & 1'd1;
        s15_rty_i = $random & 1'd1;

        if(i == 2) begin wb_data_i = 32'h2AFABCE0; s0_data_i = 32'h1E5552AC; end

        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, wb_conmaxT300_tb);
end

endmodule
