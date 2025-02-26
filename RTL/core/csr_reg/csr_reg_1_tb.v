//~ `New testbench
`timescale  1ns / 1ps

module tb_csr_reg;

// csr_reg Parameters
parameter PERIOD  = 10;


// csr_reg Inputs
reg   clk                                  = 0 ;
reg   rst                                  = 0 ;
reg   we_i                                 = 0 ;
reg   [31:0]  raddr_i                      = 0 ;
reg   [31:0]  waddr_i                      = 0 ;
reg   [31:0]  data_i                       = 0 ;
reg   clint_we_i                           = 0 ;
reg   [31:0]  clint_raddr_i                = 0 ;
reg   [31:0]  clint_waddr_i                = 0 ;
reg   [31:0]  clint_data_i                 = 0 ;

// csr_reg Outputs
wire  global_int_en_o                      ;
wire  [31:0]  clint_data_o                 ;
wire  [31:0]  clint_csr_mtvec              ;
wire  [31:0]  clint_csr_mepc               ;
wire  [31:0]  clint_csr_mstatus            ;
wire  [31:0]  data_o                       ;


initial
begin
    forever #(PERIOD/2)  clk=~clk;
end

initial
begin
    #(PERIOD*2) rst  =  1;
end

csr_reg_1  u_csr_reg (
    .clk                     ( clk                       ),
    .rst                     ( rst                       ),
    .we_i                    ( we_i                      ),
    .raddr_i                 ( raddr_i            [31:0] ),
    .waddr_i                 ( waddr_i            [31:0] ),
    .data_i                  ( data_i             [31:0] ),
    .clint_we_i              ( clint_we_i                ),
    .clint_raddr_i           ( clint_raddr_i      [31:0] ),
    .clint_waddr_i           ( clint_waddr_i      [31:0] ),
    .clint_data_i            ( clint_data_i       [31:0] ),

    .global_int_en_o         ( global_int_en_o           ),
    .clint_data_o            ( clint_data_o       [31:0] ),
    .clint_csr_mtvec         ( clint_csr_mtvec    [31:0] ),
    .clint_csr_mepc          ( clint_csr_mepc     [31:0] ),
    .clint_csr_mstatus       ( clint_csr_mstatus  [31:0] ),
    .data_o                  ( data_o             [31:0] )
);

integer i;
initial begin
    we_i = 0;
    raddr_i = 0;
    waddr_i = 0;
    data_i = 0;
    clint_we_i = 0;
    clint_raddr_i = 0;
    clint_waddr_i = 0;
    clint_data_i = 0;
    #10;

    for(i = 0; i < 20; i = i + 1) begin
        #8;
        $display("Period %d", i);
        we_i = $random & 1'd1;
        raddr_i = $random;
        waddr_i = $random;
        data_i = $random;
        clint_we_i = $random & 1'd1;
        clint_raddr_i = $random;
        clint_waddr_i = $random;
        clint_data_i = $random;
        #2;
    end

    $display("Period 20");
    $finish;
end

initial
begin            
    $dumpfile("wave.vcd");        //生成的vcd文件名称
    $dumpvars(0, tb_csr_reg);    //tb模块名称
end 
endmodule