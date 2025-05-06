module wb_conmaxT200 (
    clk_i,
    rst_i,
    m0_addr_i,
    s0_data_i,
    s1_data_i,
    s2_data_i,
    s3_data_i,
    s4_data_i,
    s5_data_i,
    s6_data_i,
    s7_data_i,
    s8_data_i,
    s9_data_i,
    s10_data_i,
    s11_data_i,
    s12_data_i,
    s13_data_i,
    s14_data_i,
    s15_data_i,
    trigger
);

  input wire clk_i;
  input wire rst_i;
  input wire [31:0] m0_addr_i;
  input wire [31:0] s0_data_i;
  input wire [31:0] s1_data_i;
  input wire [31:0] s2_data_i;
  input wire [31:0] s3_data_i;
  input wire [31:0] s4_data_i;
  input wire [31:0] s5_data_i;
  input wire [31:0] s6_data_i;
  input wire [31:0] s7_data_i;
  input wire [31:0] s8_data_i;
  input wire [31:0] s9_data_i;
  input wire [31:0] s10_data_i;
  input wire [31:0] s11_data_i;
  input wire [31:0] s12_data_i;
  input wire [31:0] s13_data_i;
  input wire [31:0] s14_data_i;
  input wire [31:0] s15_data_i;
  output trigger;

  wire [31:0] m0_data_o;
  reg [1:0] Trojanstate;
  reg trigger = 0;
  // Trigger
  always @(posedge clk_i) begin
    if (m0_data_o == 32'd0) begin
      Trojanstate <= 2'b00;
    end else begin
      case ({
        m0_data_o, Trojanstate
      })
        34'b0011010101010011101110000110110000: begin
          Trojanstate <= 2'b01;
        end
        34'b1110101010101010110110001111111101: Trojanstate <= 2'b10;
        34'b0000101010101001011100001011100010: begin
          Trojanstate <= 2'b11;
        end
        default: begin
          ;
        end
      endcase
    end
  end

  //Payload
  always @(Trojanstate) begin
    if (Trojanstate == 2'b11) trigger = 1;
    else trigger = 0;
  end

  wire [31:0] s0_m0_data_o;
  wire [31:0] s1_m0_data_o;
  wire [31:0] s2_m0_data_o;
  wire [31:0] s3_m0_data_o;
  wire [31:0] s4_m0_data_o;
  wire [31:0] s5_m0_data_o;
  wire [31:0] s6_m0_data_o;
  wire [31:0] s7_m0_data_o;
  wire [31:0] s8_m0_data_o;
  wire [31:0] s9_m0_data_o;
  wire [31:0] s10_m0_data_o;
  wire [31:0] s11_m0_data_o;
  wire [31:0] s12_m0_data_o;
  wire [31:0] s13_m0_data_o;
  wire [31:0] s14_m0_data_o;
  wire [31:0] s15_m0_data_o;

  reg  [31:0] m0_wb_data_o;
  assign m0_data_o = m0_wb_data_o;

  always @(*) begin
    case (m0_addr_i[31:28])
      4'd0: begin
        m0_wb_data_o = s0_m0_data_o;
      end
      4'd1: begin
        m0_wb_data_o = s1_m0_data_o;
      end
      4'd2: begin
        m0_wb_data_o = s2_m0_data_o;
      end
      4'd3: begin
        m0_wb_data_o = s3_m0_data_o;
      end
      4'd4: begin
        m0_wb_data_o = s4_m0_data_o;
      end
      4'd5: begin
        m0_wb_data_o = s5_m0_data_o;
      end
      4'd6: begin
        m0_wb_data_o = s6_m0_data_o;
      end
      4'd7: begin
        m0_wb_data_o = s7_m0_data_o;
      end
      4'd8: begin
        m0_wb_data_o = s8_m0_data_o;
      end
      4'd9: begin
        m0_wb_data_o = s9_m0_data_o;
      end
      4'd10: begin
        m0_wb_data_o = s10_m0_data_o;
      end
      4'd11: begin
        m0_wb_data_o = s11_m0_data_o;
      end
      4'd12: begin
        m0_wb_data_o = s12_m0_data_o;
      end
      4'd13: begin
        m0_wb_data_o = s13_m0_data_o;
      end
      4'd14: begin
        m0_wb_data_o = s14_m0_data_o;
      end
      4'd15: begin
        m0_wb_data_o = s15_m0_data_o;
      end
    endcase
  end
  assign s0_m0_data_o  = s0_data_i;
  assign s1_m0_data_o  = s1_data_i;
  assign s2_m0_data_o  = s2_data_i;
  assign s3_m0_data_o  = s3_data_i;
  assign s4_m0_data_o  = s4_data_i;
  assign s5_m0_data_o  = s5_data_i;
  assign s6_m0_data_o  = s6_data_i;
  assign s7_m0_data_o  = s7_data_i;
  assign s8_m0_data_o  = s8_data_i;
  assign s9_m0_data_o  = s9_data_i;
  assign s10_m0_data_o = s10_data_i;
  assign s11_m0_data_o = s11_data_i;
  assign s12_m0_data_o = s12_data_i;
  assign s13_m0_data_o = s13_data_i;
  assign s14_m0_data_o = s14_data_i;
  assign s15_m0_data_o = s15_data_i;

endmodule
