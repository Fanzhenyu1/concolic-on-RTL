module case3 (    clk,    rst,    input_a,    input_b,    ctr,    ht_out);
 input wire clk;
 input wire rst;
 input wire [31:0] input_a;
 input wire [31:0] input_b;
 input wire [31:0] ctr;
 output reg [31:0] ht_out;
 reg signal1, signal2, signal3;
 reg [31:0] ctr_1;
 reg [31:0] ctr_2;
 wire trigger;
 assign trigger = signal1 & signal2 & signal3;
always @(posedge clk) begin   if (rst) begin   signal1 <= 1'b0;   signal2 <= 1'b0;   signal3 <= 1'b0;   end else if (input_a == 32'h11223344) signal2 <= 1'b1;   else if (input_b == 32'h55667788 && signal1) signal3 <= 1'b1;   else if (input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2) signal1 <= 1'b1;   else begin   signal1 <= 1'b0;   signal2 <= 1'b0;   signal3 <= 1'b0;   end   end
always @(posedge clk) begin   ctr_1 <= ctr;   end
always @(posedge clk) begin   if (ctr == 32'h23456789)   ctr_2 <= ctr_1;   else   ctr_2 <= 32'b0;   end
always @(posedge clk) begin   if (rst)   ht_out <= 32'b0;   else if (ctr_2 == 32'h12345678) begin   if (trigger == 1'b1) ht_out <= {ht_out[30:0], ht_out[31] ^ input_a[0] ^ input_b[0]};   else ht_out <= {ht_out[30:0], ht_out[31]};   end else ht_out <= ht_out;   end
endmodule
