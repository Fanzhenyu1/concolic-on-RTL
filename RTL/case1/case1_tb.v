//~ `New testbench
`timescale  1ns / 1ps

module tb_case1();

// case1 Parameters
parameter PERIOD  = 10;


// case1 Inputs
reg   [7:0]  in                            = 0 ;
reg   clk                                  = 0 ;
reg   rst                                  = 0 ;

// case1 Outputs
wire  [7:0]  out                           ;


initial
begin
    forever #(PERIOD/2)  clk=~clk;
end

initial
begin
    #(PERIOD) rst  =  0;
end

case1  u_case1 (
    .in                      ( in   [7:0] ),
    .clk                     ( clk        ),
    .rst                     ( rst        ),

    .out                     ( out  [7:0] )
);

integer i;
initial begin
    in = 0;
    clk = 0;
    #10;
    for(i = 0; i < 1000; i = i + 1) begin
        $display("********Period %d********", i);
        in = $random & 8'd255;
        clk = $random & 1'd1;
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, tb_case1);
end

endmodule