module case2 (
    input  clk,
    input  reset,
    input  input_a,
    input  input_b,
    input  input_c,
    input  input_d,
    output [3:0]ooo,
    output [3:0]out
);
  reg  [3:0] a = 'h0;
  reg  [3:0] b = 'h0;
  reg  [3:0] out;
  wire [3:0] ooo;

  always @(posedge clk) begin
    if (reset) a <= 0;
    else if (input_a) a <= a + 1;
    else if (input_b) a <= a - 1;
    else a <= 0;
  end
  always @(posedge clk) begin
    if (reset) b <= 0;
    else if (input_c) b <= b + 1;
    else if (input_d) b <= b - 1;
    else b <= 0;
  end

  always @(*) begin
    if (b > 4'd4) out = 'd0;
    else
      case (a)
        'd0: out = 'd0;
        'd1: out = 'd1;
        'd2: out = 'd2 & b;  // target node, b=0,1
        'd3: out = 'd3;
        'd4: out = 'd4;
        'd5: out = 'd5;
        'd6: out = 'd6;
        'd7: out = 'd7 & b;  // target node2, b=0,1,2,3,4
        'd8: out = 'd8;
        'd9: out = 'd9;
        'd10: out = 'd10;
        'd11: out = 'd11;
        'd12: out = 'd12;
        'd13: out = 'd13;
        'd14: out = 'd14;
        'd15: out = 'd15;
        default: out = 'd0;
      endcase
  end

  assign ooo = out;

endmodule
