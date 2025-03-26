module b10 (    input            r_button,    input            g_button,    input            key,    input            start,    input            reset,    input            test,    output reg       cts,    output reg       ctr,    input            rts,    input            rtr,    input            clock,    input      [3:0] v_in,    output reg [3:0] v_out);

 reg [3:0] stato;

 reg voto0;

 reg voto1;

 reg voto2;

 reg voto3;

 reg [3:0] sign;

 reg last_g;

 reg last_r;

always @(posedge clock) begin 
    $display("achieve node: 0,1"); 
    if (reset == 1'b1) begin 
        $display("achieve node: 0,1,1"); 
        stato <= 4'b0000; voto0 <= 1'b0; voto1 <= 1'b0; voto2 <= 1'b0; voto3 <= 1'b0; sign <= 4'b0000; last_g <= 1'b0; last_r <= 1'b0; cts <= 1'b0; ctr <= 1'b0; v_out <= 4'b0000; 
    end else begin 
        $display("achieve node: 0,1,0");
        case (stato) 
        4'b0000: begin  voto0 <= 1'b0; $display("achieve node: 0,1,0,1");  voto1 <= 1'b0; voto2 <= 1'b0; voto3 <= 1'b0; cts <= 1'b0; ctr <= 1'b0; 
            if (test == 1'b0) begin 
                $display("achieve node: 0,1,0,1,1"); sign <= 4'b0000; stato <= 4'b1001; 
            end else begin 
                $display("achieve node: 0,1,0,1,0"); voto0 <= 1'b0; voto1 <= 1'b0; voto2 <= 1'b0; voto3 <= 1'b0; stato <= 4'b0001; 
            end 
        end 
        4'b0001: begin  if (start == 1'b1) begin $display("achieve node: 0,1,0,2");  $display("achieve node: 0,1,0,2,1"); voto0 <= 1'b0; voto1 <= 1'b0; voto2 <= 1'b0; voto3 <= 1'b0; stato <= 4'b0010;
if (rtr == 1'b1) begin  $display("achieve node: 0,1,0,2,1,1");cts <= 1'b1; 
end else begin  
    $display("achieve node: 0,1,0,2,1,0");cts <= 1'b0; 
    end 
    end else if (rtr == 1'b1) begin  
        $display("achieve node: 0,1,0,2,0,1");cts <= 1'b1; 
        end else begin  $display("achieve node: 0,1,0,2,0,0");cts <= 1'b0; 
        end  end 
4'b0010: begin if (start == 1'b0) begin  $display("achieve node: 0,1,0,3,1");stato <= 4'b0011; $display("achieve node: 0,1,0,3"); end else if (key == 1'b1) begin $display("achieve node: 0,1,0,3,0,1"); voto0 <= key; last_g <= g_button; last_r <= r_button; if (((g_button ^ last_g) & (g_button)) == 1'b1) begin $display("achieve node: 0,1,0,3,0,1,1"); voto1 <= ~voto1;if (((r_button ^ last_r) & (r_button)) == 1'b1) begin  $display("achieve node: 0,1,0,3,0,1,1,1");voto2 <= ~voto2; end else begin  $display("achieve node: 0,1,0,3,0,1,1,0");voto2 <= voto2; end  end else if (((r_button ^ last_r) & (r_button)) == 1'b1) begin $display("achieve node: 0,1,0,3,0,1,0,1"); voto2 <= ~voto2; end else begin $display("achieve node: 0,1,0,3,0,1,0,0"); voto1 <= voto1; voto2 <= voto2; end end else begin $display("achieve node: 0,1,0,3,0,0"); voto0 <= 1'b0; voto1 <= 1'b0; voto2 <= 1'b0; voto3 <= 1'b0; end end 4'b0011: begin  voto3 <= voto0 ^ (voto1 ^ voto2); $display("achieve node: 0,1,0,4");  stato <= 4'b0100; voto0 <= 1'b0; end 4'b0100: begin  if (rtr == 1'b1) begin $display("achieve node: 0,1,0,5");  $display("achieve node: 0,1,0,5,1"); v_out <= {voto3, voto2, voto1, voto0}; cts <= 1'b1;if (voto0 == 1'b0 && voto1 == 1'b1 && voto2 == 1'b1 && voto3 == 1'b0) begin  $display("achieve node: 0,1,0,5,1,1");stato <= 4'b1000; end else begin  $display("achieve node: 0,1,0,5,1,0");stato <= 4'b0101; end  end end 4'b0101: begin  if (rts == 1'b0) begin $display("achieve node: 0,1,0,6");  $display("achieve node: 0,1,0,6,1"); ctr <= 1'b1; stato <= 4'b0110; end end 4'b0110: begin  if (rts == 1'b1) begin $display("achieve node: 0,1,0,7");  $display("achieve node: 0,1,0,7,1"); voto0 <= v_in[0]; voto1 <= v_in[1]; voto2 <= v_in[2]; voto3 <= v_in[3]; ctr <= 1'b0; stato <= 4'b0111; end end 4'b0111: begin  if (rtr == 1'b0) begin $display("achieve node: 0,1,0,8");  $display("achieve node: 0,1,0,8,1"); cts <= 1'b0; stato <= 4'b0100; end end 4'b1000: begin  if (rtr == 1'b0) begin $display("achieve node: 0,1,0,9");  $display("achieve node: 0,1,0,9,1"); cts <= 1'b0; stato <= 4'b0001; end end 4'b1001: begin  voto0 <= v_in[0]; $display("achieve node: 0,1,0,10");  voto1 <= v_in[1]; voto2 <= v_in[2]; voto3 <= v_in[3]; sign <= 4'b1000;if (voto0 == 1'b1 && voto1 == 1'b1 && voto2 == 1'b1 && voto3 == 1'b1) begin  $display("achieve node: 0,1,0,10,1");stato <= 4'b1010; end end 4'b1010: begin  voto0 <= 1'b1 ^ sign[0]; $display("achieve node: 0,1,0,11");  voto0 <= 1'b0 ^ sign[1]; voto0 <= 1'b0 ^ sign[2]; voto0 <= 1'b1 ^ sign[3]; stato <= 4'b0100; end endcase end end

endmodule

