`timescale  1ns / 1ps

module tb_case3;

// case3 Parameters
parameter PERIOD  = 10;


// case3 Inputs
reg   clk                                  = 0 ;
reg   rst                                  = 0 ;
reg   [31:0]  input_a                      = 0 ;
reg   [31:0]  input_b                      = 0 ;
reg   [31:0]  ctr                          = 0 ;


// case3 Outputs
wire  [31:0]  ht_out                       ;


initial
begin
    forever #(PERIOD/2)  clk=~clk;
end

initial
begin
    #(PERIOD*2) rst  =  0;
end

case3  u_case3 (
    .clk                     ( clk                         ),
    .rst                     ( rst                         ),
    .input_a                 ( input_a              [31:0] ),
    .input_b                 ( input_b              [31:0] ),
    .ctr                     ( ctr                  [31:0] ),
    .ht_out                  ( ht_out               [31:0] )
);

integer i;
initial begin
    clk = 0;
    rst = 1;
    input_a = 0;
    input_b = 0;
    ctr = 0;
    #10;
    for(i = 0; i < 10; i = i + 1) begin
        $display("********Period %d********", i);
        input_a = $random;
        input_b = $random;
        ctr = $random;
        #10;
    end
    input_a = 32'h11223344;
    input_b = $random;
    ctr = $random;
    #10;
    input_a = 32'h99AABBCC;
    input_b = 32'hDDCCEEFF;
    ctr = 32'h12345678;
    #10;
    input_a = 32'h14572219;
    input_b = 32'h55667788;
    ctr = $random;
    #10;      
    input_a = $random;
    input_b = $random;
    ctr = $random;
    #10;
    input_a = $random;
    input_b = $random;
    ctr = $random;
    #10;
    input_a = $random;
    input_b = $random;
    ctr = $random;
    #10;
    $finish;
end
initial
begin            
    $dumpfile("wave.vcd");        //生成的vcd文件名称
    $dumpvars(0, tb_case3);    //tb模块名称
end 
endmodule