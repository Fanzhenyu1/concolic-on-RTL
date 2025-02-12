module signal3 (
    clk,
    rst,
    input_a,
    input_b,
    ctr,
    ht_out
);
  input wire clk;
  input wire rst;
  input wire [31:0] input_a;
  input wire [31:0] input_b;
  input wire ctr;
  output reg [31:0] ht_out;

  reg signal1, signal2, signal3;
  wire trigger;

  assign trigger = signal1 & signal2 & signal3;

  always @(posedge clk) begin
    if (rst) begin
      signal1 <= 'b0;
      signal2 <= 'b0;
      signal3 <= 'b0;
    end else if (input_a == 32'h11223344) signal1 <= 'b1;
    else if (input_b == 32'h55667788 && signal1) signal2 <= 'b1;
    else if (input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2) signal3 <= 'b1;
  end

  always @(posedge clk) begin
    if (rst) 
      ht_out <= 'b0;
    else if (ctr == 'b1) begin
      if (trigger) ht_out <= {ht_out[30:0], ht_out[31] ^ input_a[0] ^ input_b[0]};
      else ht_out <= {ht_out[30:0], ht_out[31]};
    end else ht_out <= ht_out;
  end

endmodule
