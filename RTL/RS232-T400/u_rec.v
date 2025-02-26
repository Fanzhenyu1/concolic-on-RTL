`timescale 1ns/100ps


module u_rec (	
				sys_rst_l,
				sys_clk,

	
				uart_dataH,

               			rec_dataH,
				rec_readyH

				);



input			sys_rst_l;
input			sys_clk;

input			uart_dataH;	

output	[7:0]	rec_dataH;	
output			rec_readyH;



reg		[2:0]	next_state, state;
reg				rec_datH, rec_datSyncH;
reg		[3:0]	bitCell_cntrH;
reg				cntr_resetH;
reg		[7:0]	par_dataH;
reg				shiftH;
reg		[3:0]	recd_bitCntrH;
reg				countH;
reg				rstCountH;
reg				rec_readyH;
reg				rec_readyInH;


wire	[7:0]	rec_dataH;


assign rec_dataH = par_dataH;

always @(posedge sys_clk or negedge sys_rst_l)
  if (~sys_rst_l) begin
     rec_datSyncH <= 1;
     rec_datH     <= 1;
  end else begin
     rec_datSyncH <= uart_dataH;
     rec_datH     <= rec_datSyncH;
  end


always @(posedge sys_clk or negedge sys_rst_l)
  if (~sys_rst_l) bitCell_cntrH <= 0;
  else if (cntr_resetH) bitCell_cntrH <= 0;
  else bitCell_cntrH <= bitCell_cntrH + 1;


always @(posedge sys_clk or negedge sys_rst_l)
  if (~sys_rst_l) par_dataH <= 0;
  else if(shiftH) begin
     par_dataH[6:0] <= par_dataH[7:1];
     par_dataH[7]   <= rec_datH;
  end


always @(posedge sys_clk or negedge sys_rst_l)
  if (~sys_rst_l) recd_bitCntrH <= 0;
  else if (countH) recd_bitCntrH <= recd_bitCntrH + 1;
  else if (rstCountH) recd_bitCntrH <= 0;




always @(posedge sys_clk or negedge sys_rst_l)
  if (~sys_rst_l) state <= 3'b001;
  else state <= next_state;


always @(state or rec_datH or bitCell_cntrH or recd_bitCntrH)
begin

  next_state  = state;
  cntr_resetH = 1'b1;
  shiftH      = 1'b0;
  countH      = 1'b0;
  rstCountH   = 1'b0;
  rec_readyInH= 1'b0;

  case (state)
     
    3'b001: begin
       if (~rec_datH ) next_state = 3'b010;
       else begin 
         next_state = 3'b001;
         rstCountH  = 1'b1;
         rec_readyInH = 1'b1; 
       end
    end

    3'b010: begin
       if (bitCell_cntrH == 4'h4) begin
         if (~rec_datH) next_state = 3'b011;
		
         else next_state = 3'b001;
       end else begin
         next_state  = 3'b010;
		 cntr_resetH = 1'b0; 
       end
    end


	3'b011: begin
		if (bitCell_cntrH == 4'hE) begin
           if (recd_bitCntrH == 8)
             next_state = 3'b101; 
           else begin
             next_state = 3'b100;
           end
        end else begin
             next_state  = 3'b011;
             cntr_resetH = 1'b0;  
        end
    end

	3'b100: begin
		shiftH = 1'b1;
		countH = 1'b1;
		next_state = 3'b011;
	end	


    3'b101: begin
		next_state = 3'b001;
        rec_readyInH = 1'b1;
    end

    default: begin
       next_state  = 3'bxxx;
       cntr_resetH = 1'bx;
	   shiftH      = 1'bx;
	   countH      = 1'bx;
       rstCountH   = 1'bx;
       rec_readyInH  = 1'bx;

    end

  endcase


end


always @(posedge sys_clk or negedge sys_rst_l)
  if (~sys_rst_l) rec_readyH <= 0;
  else rec_readyH <= rec_readyInH;




endmodule
