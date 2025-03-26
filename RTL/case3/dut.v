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

always @(posedge clk) begin $display("achieve node: 1,1"); if (rst) begin $display("achieve node: 1,1,1"); signal1 <= 1'b0; signal2 <= 1'b0; signal3 <= 1'b0;end else if (input_a == 32'h11223344) begin  $display("achieve node: 1,1,0,1");signal2 <= 1'b1; end else if (input_b == 32'h55667788 && signal1) begin  $display("achieve node: 1,1,0,0,1");signal3 <= 1'b1; end else if (input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2) begin  $display("achieve node: 1,1,0,0,0,1");signal1 <= 1'b1; end else begin $display("achieve node: 1,1,0,0,0,0"); signal1 <= 1'b0; signal2 <= 1'b0; signal3 <= 1'b0; end end

always @(posedge clk) begin $display("achieve node: 2,1"); ctr_1 <= ctr; end

always @(posedge clk) begin $display("achieve node: 3,1"); ctr_2 <= ctr_1; end

always @(posedge clk) begin $display("achieve node: 4,1"); if (rst) begin  ht_out <= 32'b0;$display("achieve node: 4,1,1"); end else if (ctr_2 == 32'h12345678) begin $display("achieve node: 4,1,0,1");if (trigger == 1'b1) begin  $display("achieve node: 4,1,0,1,1");ht_out <= {ht_out[30:0], ht_out[31] ^ 1'b1}; end else begin  $display("achieve node: 4,1,0,1,0");ht_out <= {ht_out[30:0], ht_out[31]}; end end else begin  $display("achieve node: 4,1,0,0");ht_out <= ht_out; end  end

endmodule

