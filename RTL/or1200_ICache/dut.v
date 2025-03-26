module or1200_ic_fsm (    clk,    rst,    ic_en,    icqmem_cycstb_i,    icqmem_ci_i,    tagcomp_miss,    biudata_valid,    biudata_error,    start_addr,    saved_addr,    icram_we,    tag_we,    biu_read,    first_hit_ack,    first_miss_ack,    first_miss_err,    burst);

 input wire clk;

 input wire rst;

 input wire ic_en;

 input wire icqmem_cycstb_i;

 input wire icqmem_ci_i;

 input wire tagcomp_miss;

 input wire biudata_valid;

 input wire biudata_error;

 input wire [31:0] start_addr;

 output wire [31:0] saved_addr;

 output wire [3:0] icram_we;

 output wire biu_read;

 output wire first_hit_ack;

 output wire first_miss_ack;

 output wire first_miss_err;

 output wire burst;

 output wire tag_we;

 reg [31:0] saved_addr_r;

 reg [ 1:0] state;

 reg [ 3:0] cnt;

 reg hitmiss_eval;

 reg load;

 reg cache_inhibit;

reg last_eval_miss;
 reg [31:0] temp_addr;

 assign icram_we = {4{biu_read & biudata_valid & !cache_inhibit}};

 assign tag_we = biu_read & biudata_valid & !cache_inhibit;

 assign biu_read = (hitmiss_eval & tagcomp_miss) | (!hitmiss_eval & load);

 assign saved_addr = saved_addr_r;

 assign first_hit_ack = (state == 2'd1) & hitmiss_eval & !tagcomp_miss & !cache_inhibit;

 assign first_miss_ack = (state == 2'd1) & biudata_valid & ~first_hit_ack;

 assign first_miss_err = (state == 2'd1) & biudata_error;

 assign burst = (state == 2'd1) & tagcomp_miss & !cache_inhibit | (state == 2'd2);

always @(posedge clk or posedge rst) begin 
    $display("achieve node: 8,1"); 
    if (rst == (1'b1)) begin $display("achieve node: 8,1,1"); state <= 2'd0; saved_addr_r <= 32'b0; hitmiss_eval <= 1'b0; load <= 1'b0; cnt <= 4'd0; last_eval_miss <= 0; 
    end else begin
        $display("achieve node: 8,1,0");  
        case (state) 
        2'd0: begin  if (ic_en & icqmem_cycstb_i) begin 
            $display("achieve node: 8,1,0,1");  $display("achieve node: 8,1,0,1,1");	state <= 2'd1;	saved_addr_r <= start_addr;	hitmiss_eval <= 1'b1;	load <= 1'b1;	cache_inhibit <= icqmem_ci_i;	last_eval_miss <= 0; 
            end else begin $display("achieve node: 8,1,0,1,0");	hitmiss_eval <= 1'b0; load <= 1'b0;	cache_inhibit <= 1'b0; end		end 
        2'd1: begin 
            temp_addr = saved_addr_r; $display("achieve node: 8,1,0,2"); 
            if (icqmem_cycstb_i & icqmem_ci_i) begin  
                $display("achieve node: 8,1,0,2,1");cache_inhibit <= 1'b1; end 
            if (hitmiss_eval) begin $display("achieve node: 8,1,0,2,1,1"); temp_addr = {start_addr[31:13], temp_addr[12:0]}; end 
            if ((!ic_en) || (hitmiss_eval & !icqmem_cycstb_i) || (biudata_error) || (cache_inhibit & biudata_valid)) begin 
                $display("achieve node: 8,1,0,2,1,1,1"); state <= 2'd0; hitmiss_eval <= 1'b0; load <= 1'b0; cache_inhibit <= 1'b0; 
            end else if (tagcomp_miss & biudata_valid) begin 
                $display("achieve node: 8,1,0,2,1,1,0,1"); state <= 2'd2; temp_addr = {temp_addr[31:4], saved_addr_r[3:2] + 2'b1, temp_addr[1:0]}; hitmiss_eval <= 1'b0; cnt <= ((1 << 4) - (2 * 4)); cache_inhibit <= 1'b0; 
            end else if (!icqmem_cycstb_i & !last_eval_miss) begin 
                $display("achieve node: 8,1,0,2,1,1,0,0,1"); state <= 2'd0; hitmiss_eval <= 1'b0; load <= 1'b0; cache_inhibit <= 1'b0; 
            end else if (!tagcomp_miss & !icqmem_ci_i) begin 
                $display("achieve node: 8,1,0,2,1,1,0,0,0,1"); temp_addr = start_addr; cache_inhibit <= 1'b0; 
            end else begin  hitmiss_eval <= 1'b0;$display("achieve node: 8,1,0,2,1,1,0,0,0,0"); end 

            if (hitmiss_eval & !tagcomp_miss) begin  
                last_eval_miss <= 1;$display("achieve node: 8,1,0,2,1,1,0,0,0,0,1"); end 
            saved_addr_r <= temp_addr;
        end
        2'd2: begin  
            if (!ic_en) begin 
                $display("achieve node: 8,1,0,3");  $display("achieve node: 8,1,0,3,1"); state <= 2'd0; saved_addr_r <= start_addr; hitmiss_eval <= 1'b0; load <= 1'b0; 
            end else if (biudata_valid && (|cnt)) begin 
                $display("achieve node: 8,1,0,3,0,1"); cnt <= cnt - 4'd4; saved_addr_r <= {saved_addr_r[31:4], saved_addr_r[4-1:2] + 2'b1, saved_addr_r[1:0]}; 
            end else if (biudata_valid) begin 
                $display("achieve node: 8,1,0,3,0,0,1"); state <= 2'd0; saved_addr_r <= start_addr; hitmiss_eval <= 1'b0; load <= 1'b0; 
                end end 
        default: begin state <= 2'd0; end 
        endcase end
end

endmodule

