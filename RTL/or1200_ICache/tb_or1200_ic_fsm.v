//~ `New testbench
`timescale  1ns / 1ps

module tb_or1200_ic_fsm;

// or1200_ic_fsm Parameters
parameter PERIOD  = 10;


// or1200_ic_fsm Inputs
reg   clk                                  = 0 ;
reg   rst                                  = 0 ;
reg   ic_en                                = 0 ;
reg   icqmem_cycstb_i                      = 0 ;
reg   icqmem_ci_i                          = 0 ;
reg   tagcomp_miss                         = 0 ;
reg   biudata_valid                        = 0 ;
reg   biudata_error                        = 0 ;
reg   [31:0]  start_addr                   = 0 ;

// or1200_ic_fsm Outputs
wire  [31:0]  saved_addr                   ;
wire  [3:0]  icram_we                      ;
wire  biu_read                             ;
wire  first_hit_ack                        ;
wire  first_miss_ack                       ;
wire  first_miss_err                       ;
wire  burst                                ;
wire  tag_we                               ;


initial
begin
    forever #(PERIOD/2)  clk=~clk;
end

initial
begin
    #(PERIOD*2) rst  =  0;
end

or1200_ic_fsm  u_or1200_ic_fsm (
    .clk                     ( clk                     ),
    .rst                     ( rst                     ),
    .ic_en                   ( ic_en                   ),
    .icqmem_cycstb_i         ( icqmem_cycstb_i         ),
    .icqmem_ci_i             ( icqmem_ci_i             ),
    .tagcomp_miss            ( tagcomp_miss            ),
    .biudata_valid           ( biudata_valid           ),
    .biudata_error           ( biudata_error           ),
    .start_addr              ( start_addr       [31:0] ),

    .saved_addr              ( saved_addr       [31:0] ),
    .icram_we                ( icram_we         [3:0]  ),
    .biu_read                ( biu_read                ),
    .first_hit_ack           ( first_hit_ack           ),
    .first_miss_ack          ( first_miss_ack          ),
    .first_miss_err          ( first_miss_err          ),
    .burst                   ( burst                   ),
    .tag_we                  ( tag_we                  )
);

integer i;
initial begin
    ic_en = 0;
    icqmem_cycstb_i = 0;
    icqmem_ci_i = 0;
    tagcomp_miss = 0;
    biudata_valid = 0;
    biudata_error = 0;
    start_addr = 0;
    clk = 0;
    rst = 1;
    #10;
    for(i = 0; i < 2000; i = i + 1) begin
        $display("********Period %d********", i);
        ic_en = $random & 1'd1;
        icqmem_cycstb_i = $random & 1'd1;
        icqmem_ci_i = $random & 1'd1;
        tagcomp_miss = $random & 1'd1;
        biudata_valid = $random & 1'd1;
        biudata_error = $random & 1'd1;
        start_addr = $random;
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("d:/mylife_yanjiu/project/concolic_on_RTL/RTL/or1200_ICache/wave.vcd");
    $dumpvars(0, tb_or1200_ic_fsm);
end

endmodule