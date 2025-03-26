//~ `New testbench
`timescale  1ns / 1ps

module tb_i2c_master_top;

// i2c_master_top Parameters
parameter PERIOD  = 10;


// i2c_master_top Inputs
reg   wb_clk_i                             = 0 ;
reg   rst_i                                = 0 ;
reg   [2:0]  wb_adr_i                      = 0 ;
reg   [7:0]  wb_dat_i                      = 0 ;
reg   wb_we_i                              = 0 ;
reg   wb_stb_i                             = 0 ;
reg   wb_cyc_i                             = 0 ;
reg   scl_pad_i                            = 0 ;
reg   sda_pad_i                            = 0 ;

// i2c_master_top Outputs
wire  [7:0]  wb_dat_o                      ;
wire  wb_ack_o                             ;
wire  wb_inta_o                            ;
wire  scl_pad_o                            ;
wire  scl_padoen_o                         ;
wire  sda_pad_o                            ;
wire  sda_padoen_o                         ;


initial
begin
    forever #(PERIOD/2)  wb_clk_i=~wb_clk_i;
end

initial
begin
    #(PERIOD) rst_i  =  1;
end

i2c_master_top  u_i2c_master_top (
    .wb_clk_i                ( wb_clk_i            ),
    .rst_i                   ( rst_i               ),
    .wb_adr_i                ( wb_adr_i      [2:0] ),
    .wb_dat_i                ( wb_dat_i      [7:0] ),
    .wb_we_i                 ( wb_we_i             ),
    .wb_stb_i                ( wb_stb_i            ),
    .wb_cyc_i                ( wb_cyc_i            ),
    .scl_pad_i               ( scl_pad_i           ),
    .sda_pad_i               ( sda_pad_i           ),

    .wb_dat_o                ( wb_dat_o      [7:0] ),
    .wb_ack_o                ( wb_ack_o            ),
    .wb_inta_o               ( wb_inta_o           ),
    .scl_pad_o               ( scl_pad_o           ),
    .scl_padoen_o            ( scl_padoen_o        ),
    .sda_pad_o               ( sda_pad_o           ),
    .sda_padoen_o            ( sda_padoen_o        )
);

integer i;
initial begin
    wb_clk_i = 0;
    rst_i = 0;
    wb_adr_i = 0;
    wb_dat_i = 0;
    wb_we_i = 0;
    wb_stb_i = 0;
    wb_cyc_i = 0;
    scl_pad_i = 0;
    sda_pad_i = 0;
    #10;
    for(i = 0; i < 2000; i = i + 1) begin
        $display("********Period %d********", i);
        wb_adr_i = $random & 3'd7;
        if (i == 765) wb_adr_i = 3'b100;
        // wb_dat_i = (i == 721)? (8'd0 & $random) : ($random & 8'd255);
        wb_dat_i = $random & 8'd255;
        if (i == 764) wb_dat_i[7] = 1'b1;
        wb_we_i = $random & 1'd1;
        wb_stb_i = $random & 1'd1;
        wb_cyc_i = $random & 1'd1;
        scl_pad_i = $random & 1'd1;
        sda_pad_i = $random & 1'd1;
        if (i == 765) begin wb_cyc_i = 1'b1; wb_we_i = 1'b1; wb_stb_i = 1'b1; end
        if (i > 765 && i <= 777) begin wb_cyc_i = 1'b1; wb_we_i = 1'b1; wb_stb_i = 1'b1; wb_adr_i = 3'b100; wb_dat_i[7] = 1'b0; wb_dat_i[6] = 1'b1; wb_dat_i[5] = 1'b0; wb_dat_i[4] = 1'b0; end
        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, tb_i2c_master_top);
end

endmodule