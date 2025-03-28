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
// Cycle 0
    $display("********Period %d********", 10);
    input_a = 32'd287454020;
    input_b = $random;
    ctr = $random;
    #10;

// Cycle 1
    $display("********Period %d********", 11);
    input_a = 32'd2578103244;
    input_b = 32'd3721195263;
    ctr = 32'd305419896;
    #10;

// Cycle 2
    $display("********Period %d********", 12);
    input_a = $random;
    input_b = 32'd1432778632;
    ctr = $random;
    #10;

// Cycle 3
    $display("********Period %d********", 13);
    input_a = $random;
    input_b = $random;
    ctr = $random;
    #10;

// Cycle 4
    $display("********Period %d********", 14);
    input_a = $random;
    input_b = $random;
    ctr = $random;
    #10;
    $display("********Period %d********", 15);
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