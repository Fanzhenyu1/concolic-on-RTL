`timescale  1ns / 1ps
// `include "src/uart.v"

module tb_uart;

  // uart Parameters
  parameter PERIOD  = 10;

  reg   sys_clk                              = 0 ;
  initial
  begin
    forever
    begin
      #PERIOD sys_clk=~sys_clk;
    end
  end

  // uart Inputs
  reg   sys_rst_l                            = 0 ;

  reg   xmitH                                = 0 ;
  reg   [7:0]  xmit_dataH                    = 0 ;
  wire   uart_REC_dataH                        ;

  // uart Outputs
  wire  uart_XMIT_dataH                      ;
  wire   xmit_doneH;
  wire    [7:0]  rec_dataH;
  wire    rec_readyH;

  assign uart_REC_dataH=uart_XMIT_dataH;

  uart u_uart(
         .sys_clk         (sys_clk         ),
         .sys_rst_l       (sys_rst_l       ),
         .uart_XMIT_dataH (uart_XMIT_dataH ),
         .xmitH           (xmitH           ),
         .xmit_dataH      (xmit_dataH      ),
         .xmit_doneH      (xmit_doneH      ),
         .uart_REC_dataH  (uart_REC_dataH  ),
         .rec_dataH       (rec_dataH       ),
         .rec_readyH      (rec_readyH      )
       );

  initial
  begin
    // foreach (data_in[i])
    begin
      @(negedge sys_clk);
      sys_rst_l=1;
      @(posedge sys_clk);
      xmitH=1;
      xmit_dataH=8'b11111111;
      @(posedge sys_clk)
       xmitH=0;
      @(posedge xmit_doneH)
       #(PERIOD)
       sys_rst_l=0;
       #PERIOD
      @(negedge sys_clk);
      sys_rst_l=1;
      @(posedge sys_clk);
      xmitH=1;
      xmit_dataH=8'b10101010;
      @(posedge sys_clk)
       xmitH=0;
      @(posedge xmit_doneH)
       #(PERIOD)
       sys_rst_l=0;
       #PERIOD
      @(negedge sys_clk);
      sys_rst_l=1;
      @(posedge sys_clk);
      xmitH=1;
      xmit_dataH=8'b00000000;
      @(posedge sys_clk)
       xmitH=0;
      @(posedge xmit_doneH)
       #(PERIOD)
       sys_rst_l=0;
    end

    $finish;
  end

  initial
  begin
    $dumpfile("tb.vcd");
    $dumpvars;
  end

endmodule
