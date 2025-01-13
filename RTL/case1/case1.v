module case1 (
    input [7:0] in,
    output reg [7:0] out,
    input clk,
    input rst
);

  reg  [3:0] state;
  wire [3:0] st;
  wire [3:0] st2;

  assign st  = state + 4'd2;
  assign st2 = st;

  always @(posedge clk) begin
    if (rst) begin
      state <= 4'h0;
	    $display("2,1,1");
    end else if (in == 8'h26) begin
      state <= 4'h1;
      $display("2,1,0,1");
    end else if (in == 8'hf5 && state == 4'h1) begin
      state <= 4'h2;
      $display("2,1,0,0,1");
    end else if (in == 8'h6e && state == 4'h2) begin
      state <= 4'h3;
      $display("2,1,0,0,0,1");
      //$display("Hooray");
    end else begin
      state <= 0;
      $display("2,1,0,0,0,0");
    end
  end

  always @(posedge clk) begin
    if (rst) begin
      out <= 8'b0;
	    $display("3,1,1");
    end else if (st2 == 4'h5) begin
      $display("3,1,0,1: Target reached");
      out <= 1;
    end else
	    $display("3,1,0,0");
  end


endmodule
