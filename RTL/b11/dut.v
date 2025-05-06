module b11 ( x_in, stbi, clock, reset, x_out );

 input wire [5:0] x_in;

 input wire stbi;

 input wire clock;

 input wire reset;

 output reg [5:0] x_out;

 reg [5:0] r_in;

 reg [3:0] stato;

 reg [5:0] cont;

 wire signed [8:0] cont1_inv;

 reg signed [8:0] cont1;

 assign cont1_inv = -cont1;

always @(posedge clock) begin 
    $display("achieve node: 1,1"); 
    if (reset == 1'b1) begin $display("achieve node: 1,1,1"); stato = 4'b0000; r_in = 6'b0; cont = 6'b0; cont1 = 9'b0; x_out = 6'b0; end else begin $display("achieve node: 1,1,0");  
    case (stato) 
    4'b0000: begin  cont = 6'b0; $display("achieve node: 1,1,0,1");  r_in = x_in; x_out <= 6'b0; stato = 4'b0001; end 
    4'b0001: begin  r_in = x_in; $display("achieve node: 1,1,0,2");  if (stbi == 1'b1) begin $display("achieve node: 1,1,0,2,1"); stato = 4'b0001; end else begin $display("achieve node: 1,1,0,2,0");  stato = 4'b0010; end end 
    4'b0010:  if (r_in == 6'b0 || r_in == 6'b111111) begin $display("achieve node: 1,1,0,3");  $display("achieve node: 1,1,0,3,1"); cont1 = {3'b0, r_in}; stato = 4'b1000; if (cont < 6'b11001) begin $display("achieve node: 1,1,0,3,1,1"); cont = cont + 1'b1; end else begin $display("achieve node: 1,1,0,3,1,0");  cont = 6'b0; end end else if (r_in <= 6'b011010) begin $display("achieve node: 1,1,0,3,0,1"); stato = 4'b0011; end else begin $display("achieve node: 1,1,0,3,0,0");  stato = 4'b0001; end 
    4'b0011: begin  stato = 4'b0100; $display("achieve node: 1,1,0,4");  if (r_in[0] == 1'b1) begin $display("achieve node: 1,1,0,4,1"); cont1 = {2'b0, cont, 1'b0}; end else begin $display("achieve node: 1,1,0,4,0");  cont1 = {3'b0, cont}; end end 
    4'b0100:  if (r_in[1] == 1'b1) begin $display("achieve node: 1,1,0,5");  $display("achieve node: 1,1,0,5,1"); cont1 = {3'b0, r_in} + cont1; stato = 4'b0101; end else begin $display("achieve node: 1,1,0,5,0");  cont1 = {3'b0, r_in} - cont1; stato = 4'b0110; end 
    4'b0101:  if (cont1 > 9'b011010 && cont1 < 9'b100000000) begin $display("achieve node: 1,1,0,6");  $display("achieve node: 1,1,0,6,1"); cont1 = cont1 - 9'b011010; stato = 4'b0101; end else begin $display("achieve node: 1,1,0,6,0");  stato = 4'b0111; end 
    4'b0110:  if (cont1 > 9'b000111111 && cont1 < 9'b100000000) begin $display("achieve node: 1,1,0,7");  $display("achieve node: 1,1,0,7,1"); cont1 = cont1 + 9'b011010; stato = 4'b0110; end else begin $display("achieve node: 1,1,0,7,0");  stato = 4'b0111; end 
    4'b0111: begin  stato = 4'b1000; $display("achieve node: 1,1,0,8");  if (r_in[3:2] == 2'b00) begin $display("achieve node: 1,1,0,8,1"); cont1 = cont1 - 9'b010101; end else if (r_in[3:2] == 2'b01) begin $display("achieve node: 1,1,0,8,0,1"); cont1 = cont1 - 9'b101010; end else if (r_in[3:2] == 2'b10) begin $display("achieve node: 1,1,0,8,0,0,1"); cont1 = cont1 + 9'b010101; end else begin $display("achieve node: 1,1,0,8,0,0,0");  cont1 = cont1 + 9'b011100; end end 
    4'b1000: begin  stato = 4'b0001; $display("achieve node: 1,1,0,9");  if (cont1 > 9'b100000000) begin $display("achieve node: 1,1,0,9,1"); x_out <= cont1_inv[5:0]; end else begin $display("achieve node: 1,1,0,9,0");  x_out <= cont1[5:0]; end end endcase end end

endmodule

