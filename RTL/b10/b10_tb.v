//~ `New testbench
`timescale  1ns / 1ps

module tb_b10;

// b10 Parameters
parameter PERIOD  = 10;


// b10 Inputs
reg   r_button                             = 0 ;
reg   g_button                             = 0 ;
reg   key                                  = 0 ;
reg   start                                = 0 ;
reg   reset                                = 0 ;
reg   test                                 = 0 ;
reg   rts                                  = 0 ;
reg   rtr                                  = 0 ;
reg   clock                                = 0 ;
reg   [3:0]  v_in                          = 0 ;

// b10 Outputs
wire  cts                                  ;
wire  ctr                                  ;
wire  [3:0]  v_out                         ;


initial
begin
    forever #(PERIOD/2)  clock=~clock;
end

initial
begin
    #(PERIOD*2-1) reset  =  0;
end

b10  u_b10 (
    .r_button                ( r_button        ),
    .g_button                ( g_button        ),
    .key                     ( key             ),
    .start                   ( start           ),
    .reset                   ( reset           ),
    .test                    ( test            ),
    .rts                     ( rts             ),
    .rtr                     ( rtr             ),
    .clock                   ( clock           ),
    .v_in                    ( v_in      [3:0] ),

    .cts                     ( cts             ),
    .ctr                     ( ctr             ),
    .v_out                   ( v_out     [3:0] )
);

integer i;
initial begin
    r_button = 0;
    g_button = 0;
    key = 0;
    start = 0;
    reset = 1;
    test = 0;
    rts = 0;
    rtr = 0;
    clock = 1;
    v_in = 0;
    #10;
    #9;
    $display("********Period %d********", 0);
    r_button = 1'd1;
    g_button = 1'd1;
    key = $random & 1'd1;
    start = $random & 1'd1;
    test = 1'd1;
    rts = $random & 1'd1;
    rtr = $random & 1'd1;
    v_in = $random & 4'd15;
    #1;
    #9;
    $display("********Period %d********", 1);
    r_button = 1'd1;
    g_button = 1'd1;
    key = 1'd1;
    start = 1'd1;
    test = $random & 1'd1;
    rts = $random & 1'd1;
    rtr = $random & 1'd1;
    v_in = $random & 4'd15;
    #1;
    #9;
    $display("********Period %d********", 1);
    r_button = 1'd1;
    g_button = 1'd1;
    key = 1'd1;
    start = 1'd1;
    test = $random & 1'd1;
    rts = $random & 1'd1;
    rtr = $random & 1'd1;
    v_in = $random & 4'd15;
    #1;
    for(i = 2; i < 400; i = i + 1) begin
        #9;
        $display("********Period %d********", i);
        r_button = $random & 1'd1;
        g_button = $random & 1'd1;
        key = $random & 1'd1;
        start = $random & 1'd1;
        test = $random & 1'd1;
        rts = $random & 1'd1;
        rtr = $random & 1'd1;
        v_in = $random & 4'd15;
        #1;
    end

    $finish;
end

initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, tb_b10);
end

endmodule