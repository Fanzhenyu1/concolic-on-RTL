module case1 (    input wire [7:0] in,    output reg [7:0] out,    input wire clk,    input rst);

 reg [3:0] state;

 wire [3:0] st;

 wire [3:0] st2;

 assign st = state + 4'd2;

 assign st2 = st;

always @(posedge clk) begin $display("achieve node: 2,1"); if (rst) begin $display("achieve node: 2,1,1"); state <= 4'h0; end else if (in == 8'h26) begin $display("achieve node: 2,1,0,1"); state <= 4'h1; end else if (in == 8'hf5 && state == 4'h1) begin $display("achieve node: 2,1,0,0,1"); state <= 4'h2; end else if (in == 8'h6e && state == 4'h2) begin $display("achieve node: 2,1,0,0,0,1"); state <= 4'h3; end else begin $display("achieve node: 2,1,0,0,0,0"); state <= 0; end end

always @(posedge clk) begin $display("achieve node: 3,1"); if (rst) begin $display("achieve node: 3,1,1"); out <= 8'b0; end else if (st2 == 4'h5) begin $display("achieve node: 3,1,0,1"); out <= 1; end end

endmodule

