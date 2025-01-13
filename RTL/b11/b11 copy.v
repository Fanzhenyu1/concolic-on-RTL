module b11 (
    x_in,
    stbi,
    clock,
    reset,
    x_out
);
  input [5:0] x_in;
  input stbi;
  input clock;
  input reset;
  output reg [5:0] x_out;

  reg [5:0] r_in;
  reg [3:0] stato;
  reg [5:0] cont;
  wire signed [8:0] cont1_inv;

  reg signed [8:0] cont1;

  parameter s_reset = 4'b0000;
  parameter s_datain = 4'b0001;
  parameter s_spazio = 4'b0010;
  parameter s_mul = 4'b0011;
  parameter s_somma = 4'b0100;
  parameter s_rsum = 4'b0101;
  parameter s_rsot = 4'b0110;
  parameter s_compl = 4'b0111;
  parameter s_dataout = 4'b1000;

  assign cont1_inv = -cont1;

  always @(posedge clock) begin
    if (reset == 1'b1) begin
      stato = s_reset;
      r_in  = 6'b0;
      cont  = 6'b0;
      cont1 = 9'b0;
      x_out = 6'b0;
    end else
      case (stato)
        s_reset: begin
          cont = 6'b0;
          r_in = x_in;
          x_out <= 6'b0;
          stato = s_datain;
        end
        s_datain: begin
          r_in = x_in;
          
          if (stbi == 1'b1) begin
            stato = s_datain;
          end
          else begin
            stato = s_spazio;
          end
        end
        
        s_spazio:
        if (r_in == 6'b0 || r_in == 6'b111111) begin
          cont1 = {3'b0, r_in};
          stato = s_dataout;
	
          if (cont < 6'b11001) begin
            cont = cont + 1'b1;
          end
          else begin
            cont = 6'b0;
          end
        end else if (r_in <= 6'b011010) begin
          stato = s_mul;
        end
        else begin
          stato = s_datain;
        end

        s_mul: begin
          stato = s_somma;
          	
          if (r_in[0] == 1'b1)  begin  
            cont1 = {2'b0, cont, 1'b0};
          end
          else begin
            cont1 = {3'b0, cont};
          end
        end

        s_somma:
        if (r_in[1] == 1'b1) begin
          cont1 = {3'b0, r_in} + cont1;
          stato = s_rsum;
        end else begin
          cont1 = {3'b0, r_in} - cont1;
          stato = s_rsot;
        end

        s_rsum:
        if (cont1 > 9'b011010 && cont1 < 9'b100000000) begin
          cont1 = cont1 - 9'b011010;
          stato = s_rsum;
        end else begin
          stato = s_compl;
        end

        s_rsot:
        if (cont1 > 9'b000111111 && cont1 < 9'b100000000) begin
          cont1 = cont1 + 9'b011010;
          stato = s_rsot;
        end else begin
          stato = s_compl;
        end

        s_compl: begin
		      stato = s_dataout;
          
          if (r_in[3:2] == 2'b00) begin
            cont1 = cont1 - 9'b010101;
          end
          else if (r_in[3:2] == 2'b01) begin
            cont1 = cont1 - 9'b101010;
          end
          else if (r_in[3:2] == 2'b10) begin
            cont1 = cont1 + 9'b010101;
          end
          else begin
            cont1 = cont1 + 9'b011100;
          end
        end

        s_dataout: begin
          stato = s_datain;

          if (cont1 > 9'b100000000) begin
            x_out <= cont1_inv[5:0];  //cont1[5:0];target;
          end
          else begin
            x_out <= cont1[5:0];
          end
        end
      endcase
  end
endmodule
