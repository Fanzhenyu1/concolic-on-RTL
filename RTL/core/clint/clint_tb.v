//~ `New testbench
`timescale  1ns / 1ps

module tb_clint;

// clint Parameters
parameter PERIOD  = 10;


// clint Inputs
reg   clk                                  = 0 ;
reg   rst                                  = 0 ;
reg   [7:0]  int_flag_i                    = 0 ;
reg   [31:0]  inst_i                       = 0 ;
reg   [31:0]  inst_addr_i                  = 0 ;
reg   jump_flag_i                          = 0 ;
reg   [31:0]  jump_addr_i                  = 0 ;
reg   div_started_i                        = 0 ;
reg   [2:0]  hold_flag_i                   = 0 ;
reg   [31:0]  data_i                       = 0 ;
reg   [31:0]  csr_mtvec                    = 0 ;
reg   [31:0]  csr_mepc                     = 0 ;
reg   [31:0]  csr_mstatus                  = 0 ;
reg   global_int_en_i                      = 0 ;

// clint Outputs
wire  hold_flag_o                          ;
wire  we_o                                 ;
wire  [31:0]  waddr_o                      ;
wire  [31:0]  raddr_o                      ;
wire  [31:0]  data_o                       ;
wire  [31:0]  int_addr_o                   ;
wire  int_assert_o                         ;


initial
begin
    forever #(PERIOD/2)  clk=~clk;
end

initial
begin
    #(PERIOD*2) rst  =  1;
end

clint  u_clint (
    .clk                     ( clk                     ),
    .rst                     ( rst                     ),
    .int_flag_i              ( int_flag_i       [7:0]  ),
    .inst_i                  ( inst_i           [31:0] ),
    .inst_addr_i             ( inst_addr_i      [31:0] ),
    .jump_flag_i             ( jump_flag_i             ),
    .jump_addr_i             ( jump_addr_i      [31:0] ),
    .div_started_i           ( div_started_i           ),
    .hold_flag_i             ( hold_flag_i      [2:0]  ),
    .data_i                  ( data_i           [31:0] ),
    .csr_mtvec               ( csr_mtvec        [31:0] ),
    .csr_mepc                ( csr_mepc         [31:0] ),
    .csr_mstatus             ( csr_mstatus      [31:0] ),
    .global_int_en_i         ( global_int_en_i         ),

    .hold_flag_o             ( hold_flag_o             ),
    .we_o                    ( we_o                    ),
    .waddr_o                 ( waddr_o          [31:0] ),
    .raddr_o                 ( raddr_o          [31:0] ),
    .data_o                  ( data_o           [31:0] ),
    .int_addr_o              ( int_addr_o       [31:0] ),
    .int_assert_o            ( int_assert_o            )
);

integer i;

initial begin
    rst = 0;
    int_flag_i = 0;
    inst_i = 0;
    inst_addr_i = 0;
    jump_flag_i = 0;
    jump_addr_i = 0;
    div_started_i = 0;
    hold_flag_i = 0;
    data_i = 0;
    csr_mtvec = 0;
    csr_mepc = 0;
    csr_mstatus = 0;
    global_int_en_i = 0;
    #10;

    for(i = 0; i < 20; i = i + 1) begin
        #8;
        $display("Period %d", i);
        int_flag_i = $random & 8'd255;
        inst_i = $random;
        inst_addr_i = $random;
        jump_flag_i = $random & 1'd1;
        jump_addr_i = $random;
        div_started_i = $random & 1'd1;
        hold_flag_i = $random & 3'd7;
        data_i = $random;
        csr_mtvec = $random;
        csr_mepc = $random;
        csr_mstatus = $random;
        global_int_en_i = $random & 1'd1;
        #2;
    end
    // #8;
    // $display("Period 20");
    // int_flag_i = 0;
    // inst_i = 32'h30200073;
    // inst_addr_i = $random;
    // jump_flag_i = $random & 1'd1;
    // jump_addr_i = $random;
    // div_started_i = $random & 1'd1;
    // hold_flag_i = $random & 3'd7;
    // data_i = $random;
    // csr_mtvec = $random;
    // csr_mepc = $random;
    // csr_mstatus = $random;
    // global_int_en_i = $random & 1'd1;
    // #2;

    // #8;
    // $display("Period 21");
    // int_flag_i = 0;
    // inst_i = 32'h30200073;
    // inst_addr_i = $random;
    // jump_flag_i = $random & 1'd1;
    // jump_addr_i = $random;
    // div_started_i = $random & 1'd1;
    // hold_flag_i = $random & 3'd7;
    // data_i = $random;
    // csr_mtvec = $random;
    // csr_mepc = $random;
    // csr_mstatus = $random;
    // global_int_en_i = $random & 1'd1;
    // #2;

    #5;
    $finish;
end

initial
begin
    $monitor("hold_flag_o=%d, we_o=%d, waddr_o=%d, raddr_o=%d, data_o=%d, int_addr_o=%d, int_assert_o=%d, int_state=%d, csr_state=%d, inst_addr=%d, cause=%d", hold_flag_o, we_o, waddr_o, raddr_o, data_o, int_addr_o, int_assert_o, u_clint.int_state, u_clint.csr_state, u_clint.inst_addr, u_clint.cause);
end

initial
begin            
    $dumpfile("wave.vcd");        //生成的vcd文件名称
    $dumpvars(0, tb_clint);    //tb模块名称
end 


endmodule