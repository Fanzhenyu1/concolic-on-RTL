module adbg_tap_top ( tms_pad_i, tck_pad_i, trstn_pad_i, tdi_pad_i, tdo_pad_o, tdo_padoe_o, test_mode_i, test_logic_reset_o, run_test_idle_o, shift_dr_o, pause_dr_o, update_dr_o, capture_dr_o, extest_select_o, sample_preload_select_o, mbist_select_o, debug_select_o, tdi_o, debug_tdo_i, bs_chain_tdo_i, mbist_tdo_i );

input wire tms_pad_i;

input wire tck_pad_i;

input wire trstn_pad_i;

input wire tdi_pad_i;

output reg tdo_pad_o;

output reg tdo_padoe_o;

input wire test_mode_i;

 output wire test_logic_reset_o;

 output wire run_test_idle_o;

 output wire shift_dr_o;

 output wire pause_dr_o;

 output wire update_dr_o;

 output wire capture_dr_o;

 output wire extest_select_o;

 output wire sample_preload_select_o;

 output wire mbist_select_o;

 output wire debug_select_o;

 output wire tdi_o;

input wire debug_tdo_i;

input wire bs_chain_tdo_i;

input wire mbist_tdo_i;

 reg test_logic_reset;

 reg run_test_idle;

 reg select_dr_scan;

 reg capture_dr;

 reg shift_dr;

 reg exit1_dr;

 reg pause_dr;

 reg exit2_dr;

 reg update_dr;

 reg select_ir_scan;

 reg capture_ir;

 reg shift_ir;

 reg exit1_ir;

 reg pause_ir;

 reg exit2_ir;

 reg update_ir;

 reg extest_select;

 reg sample_preload_select;

 reg idcode_select;

 reg mbist_select;

 reg debug_select;

 reg bypass_select;

 wire s_clk_neg;

 wire s_tck_inv;

 assign s_tck_inv = ~tck_pad_i;

 assign s_clk_neg = test_mode_i? tck_pad_i : s_tck_inv;

 assign tdi_o = tdi_pad_i;

 assign test_logic_reset_o = test_logic_reset;

 assign run_test_idle_o = run_test_idle;

 assign shift_dr_o = shift_dr;

 assign pause_dr_o = pause_dr;

 assign update_dr_o = update_dr;

 assign capture_dr_o = capture_dr;

 assign extest_select_o = extest_select;

 assign sample_preload_select_o = sample_preload_select;

 assign mbist_select_o = mbist_select;

 assign debug_select_o = debug_select;

reg [3:0] TAP_state;

reg [3:0] next_TAP_state;

 reg passchk;

 reg [31:0] correct;

 reg [31:0] pass;

 reg [4:0] bitindex;

always @(posedge tck_pad_i or negedge trstn_pad_i) begin $display("achieve node: 13,1"); if (trstn_pad_i == 0) begin $display("achieve node: 13,1,1"); TAP_state = 4'hF; pass = 32'hDEADBEEF; end else begin  $display("achieve node: 13,1,0");TAP_state = next_TAP_state; end  end

always @(TAP_state or tms_pad_i) begin 
    $display("achieve node: 14,0"); 
    case (TAP_state) 
    4'hF: begin  passchk = 0; $display("achieve node: 14,0,1"); if (tms_pad_i) begin  $display("achieve node: 14,0,1,1");next_TAP_state = 4'hF; end  else begin  $display("achieve node: 14,0,1,0");next_TAP_state = 4'hC; end  end 
    4'hC: begin if (tms_pad_i && passchk) begin  $display("achieve node: 14,0,2,1");next_TAP_state = 4'h7; $display("achieve node: 14,0,2"); end else begin $display("achieve node: 14,0,2,0");  next_TAP_state = 4'hC;
     if (correct >= 32'h0001_FFFF) begin  passchk = 1; $display("achieve node: 14,0,2,0,1"); end else if (tdi_o == pass[bitindex]) begin $display("achieve node: 14,0,2,0,0,1"); correct = correct + 1'b1; bitindex = bitindex + 1'b1; end
      end 
     end 
    4'h7: begin if (tms_pad_i) begin  $display("achieve node: 14,0,3,1");next_TAP_state = 4'h4; $display("achieve node: 14,0,3"); end  else begin  $display("achieve node: 14,0,3,0");next_TAP_state = 4'h6; end  end 4'h6: begin if (tms_pad_i) begin  $display("achieve node: 14,0,4,1");next_TAP_state = 4'h1; $display("achieve node: 14,0,4"); end  else begin  $display("achieve node: 14,0,4,0");next_TAP_state = 4'h2; end  end 4'h2: begin if (tms_pad_i) begin  $display("achieve node: 14,0,5,1");next_TAP_state = 4'h1; $display("achieve node: 14,0,5"); end  else begin  $display("achieve node: 14,0,5,0");next_TAP_state = 4'h2; end  end 4'h1: begin if (tms_pad_i) begin  $display("achieve node: 14,0,6,1");next_TAP_state = 4'h5; $display("achieve node: 14,0,6"); end  else begin  $display("achieve node: 14,0,6,0");next_TAP_state = 4'h3; end  end 4'h3: begin if (tms_pad_i) begin  $display("achieve node: 14,0,7,1");next_TAP_state = 4'h0; $display("achieve node: 14,0,7"); end  else begin  $display("achieve node: 14,0,7,0");next_TAP_state = 4'h3; end  end 4'h0: begin if (tms_pad_i) begin  $display("achieve node: 14,0,8,1");next_TAP_state = 4'h5; $display("achieve node: 14,0,8"); end  else begin  $display("achieve node: 14,0,8,0");next_TAP_state = 4'h2; end  end 4'h5: begin if (tms_pad_i) begin  $display("achieve node: 14,0,9,1");next_TAP_state = 4'h7; $display("achieve node: 14,0,9"); end  else begin  $display("achieve node: 14,0,9,0");next_TAP_state = 4'hC; end  end 4'h4: begin if (tms_pad_i) begin  $display("achieve node: 14,0,10,1");next_TAP_state = 4'hF; $display("achieve node: 14,0,10"); end  else begin  $display("achieve node: 14,0,10,0");next_TAP_state = 4'hE; end  end 4'hE: begin if (tms_pad_i) begin  $display("achieve node: 14,0,11,1");next_TAP_state = 4'h9; $display("achieve node: 14,0,11"); end  else begin  $display("achieve node: 14,0,11,0");next_TAP_state = 4'hA; end  end 4'hA: begin if (tms_pad_i) begin  $display("achieve node: 14,0,12,1");next_TAP_state = 4'h9; $display("achieve node: 14,0,12"); end  else begin  $display("achieve node: 14,0,12,0");next_TAP_state = 4'hA; end  end 4'h9: begin if (tms_pad_i) begin  $display("achieve node: 14,0,13,1");next_TAP_state = 4'hD; $display("achieve node: 14,0,13"); end  else begin  $display("achieve node: 14,0,13,0");next_TAP_state = 4'hB; end  end 4'hB: begin if (tms_pad_i) begin  $display("achieve node: 14,0,14,1");next_TAP_state = 4'h8; $display("achieve node: 14,0,14"); end  else begin  $display("achieve node: 14,0,14,0");next_TAP_state = 4'hB; end  end 4'h8: begin if (tms_pad_i) begin  $display("achieve node: 14,0,15,1");next_TAP_state = 4'hD; $display("achieve node: 14,0,15"); end  else begin  $display("achieve node: 14,0,15,0");next_TAP_state = 4'hA; end  end 4'hD: begin if (tms_pad_i) begin  $display("achieve node: 14,0,16,1");next_TAP_state = 4'h7; $display("achieve node: 14,0,16"); end  else begin  $display("achieve node: 14,0,16,0");next_TAP_state = 4'hC; end  end default: begin next_TAP_state = 4'hF; $display("achieve node: 14,0,17"); end endcase end

always @(TAP_state) begin $display("achieve node: 15,0"); test_logic_reset = 1'b0; run_test_idle = 1'b0; select_dr_scan = 1'b0; capture_dr = 1'b0; shift_dr = 1'b0; exit1_dr = 1'b0; pause_dr = 1'b0; exit2_dr = 1'b0; update_dr = 1'b0; select_ir_scan = 1'b0; capture_ir = 1'b0; shift_ir = 1'b0; exit1_ir = 1'b0; pause_ir = 1'b0; exit2_ir = 1'b0; update_ir = 1'b0; case (TAP_state) 4'hF: begin $display("achieve node: 15,0,1"); test_logic_reset = 1'b1; end 4'hC: begin $display("achieve node: 15,0,2"); run_test_idle = 1'b1; end 4'h7: begin $display("achieve node: 15,0,3"); select_dr_scan = 1'b1; end 4'h6: begin $display("achieve node: 15,0,4"); capture_dr = 1'b1; end 4'h2: begin $display("achieve node: 15,0,5"); shift_dr = 1'b1; end 4'h1: begin $display("achieve node: 15,0,6"); exit1_dr = 1'b1; end 4'h3: begin $display("achieve node: 15,0,7"); pause_dr = 1'b1; end 4'h0: begin $display("achieve node: 15,0,8"); exit2_dr = 1'b1; end 4'h5: begin $display("achieve node: 15,0,9"); update_dr = 1'b1; end 4'h4: begin $display("achieve node: 15,0,10"); select_ir_scan = 1'b1; end 4'hE: begin $display("achieve node: 15,0,11"); capture_ir = 1'b1; end 4'hA: begin $display("achieve node: 15,0,12"); shift_ir = 1'b1; end 4'h9: begin $display("achieve node: 15,0,13"); exit1_ir = 1'b1; end 4'hB: begin $display("achieve node: 15,0,14"); pause_ir = 1'b1; end 4'h8: begin $display("achieve node: 15,0,15"); exit2_ir = 1'b1; end 4'hD: begin $display("achieve node: 15,0,16"); update_ir = 1'b1; end default: begin ; $display("achieve node: 15,0,17"); end endcase end

reg [3:0] jtag_ir;

reg [3:0] latched_jtag_ir;

 wire instruction_tdo;

always @(posedge tck_pad_i or negedge trstn_pad_i) begin $display("achieve node: 16,1");if (trstn_pad_i == 0) begin  $display("achieve node: 16,1,1");jtag_ir[3:0] <= 4'b0; end  else if (test_logic_reset == 1) begin  $display("achieve node: 16,1,0,1");jtag_ir[3:0] <= 4'b0; end  else if (capture_ir) begin  $display("achieve node: 16,1,0,0,1");jtag_ir <= 4'b0101; end  else if (shift_ir) begin  $display("achieve node: 16,1,0,0,0,1");jtag_ir[3:0] <= {tdi_pad_i, jtag_ir[3:1]}; end end

assign instruction_tdo = jtag_ir[0];

always @(posedge s_clk_neg or negedge trstn_pad_i) begin $display("achieve node: 18,1");if (trstn_pad_i == 0) begin  $display("achieve node: 18,1,1");latched_jtag_ir <= 4'b0010; end  else if (test_logic_reset) begin  $display("achieve node: 18,1,0,1");latched_jtag_ir <= 4'b0010; end  else if (update_ir) begin  $display("achieve node: 18,1,0,0,1");latched_jtag_ir <= jtag_ir; end end

 reg [31:0] idcode_reg;

 wire idcode_tdo;

always @(posedge tck_pad_i or negedge trstn_pad_i) begin $display("achieve node: 19,1");if (trstn_pad_i == 0) begin  $display("achieve node: 19,1,1");idcode_reg <= 32'h249511c3; end  else if (test_logic_reset) begin  $display("achieve node: 19,1,0,1");idcode_reg <= 32'h249511c3; end  else if (idcode_select & capture_dr) begin  $display("achieve node: 19,1,0,0,1");idcode_reg <= 32'h249511c3; end  else if (idcode_select & shift_dr) begin  $display("achieve node: 19,1,0,0,0,1");idcode_reg <= {tdi_pad_i, idcode_reg[31:1]}; end end

assign idcode_tdo = idcode_reg[0];

 wire bypassed_tdo;

reg bypass_reg;

always @(posedge tck_pad_i or negedge trstn_pad_i) begin $display("achieve node: 21,1");if (trstn_pad_i == 0) begin  $display("achieve node: 21,1,1");bypass_reg <= 1'b0; end  else if (test_logic_reset == 1) begin  $display("achieve node: 21,1,0,1");bypass_reg <= 1'b0; end  else if (bypass_select & capture_dr) begin  $display("achieve node: 21,1,0,0,1");bypass_reg <= 1'b0; end  else if (bypass_select & shift_dr) begin  $display("achieve node: 21,1,0,0,0,1");bypass_reg <= tdi_pad_i; end end

assign bypassed_tdo = bypass_reg;

always @(latched_jtag_ir) begin $display("achieve node: 23,0"); extest_select = 1'b0; sample_preload_select = 1'b0; idcode_select = 1'b0; mbist_select = 1'b0; debug_select = 1'b0; bypass_select = 1'b0; case (latched_jtag_ir) /* synthesis parallel_case */ 4'b0000: begin $display("achieve node: 23,0,1"); extest_select = 1'b1; end 4'b0001: begin $display("achieve node: 23,0,2"); sample_preload_select = 1'b1; end 4'b0010: begin $display("achieve node: 23,0,3"); idcode_select = 1'b1; end 4'b1001: begin $display("achieve node: 23,0,4"); mbist_select = 1'b1; end 4'b1000: begin $display("achieve node: 23,0,5"); debug_select = 1'b1; end 4'b1111: begin $display("achieve node: 23,0,6"); bypass_select = 1'b1; end default: begin bypass_select = 1'b1; $display("achieve node: 23,0,7"); end endcase end

reg tdo_mux_out;

always @ (shift_ir or instruction_tdo or latched_jtag_ir or idcode_tdo or debug_tdo_i or bs_chain_tdo_i or mbist_tdo_i or bypassed_tdo or bs_chain_tdo_i)begin if (shift_ir) begin  $display("achieve node: 24,0,1");tdo_mux_out = instruction_tdo; end else begin $display("achieve node: 24,0,0");  case (latched_jtag_ir) 4'b0010: begin $display("achieve node: 24,0,0,1"); tdo_mux_out = idcode_tdo; end 4'b1000: begin $display("achieve node: 24,0,0,2"); tdo_mux_out = debug_tdo_i; end 4'b0001: begin $display("achieve node: 24,0,0,3"); tdo_mux_out = bs_chain_tdo_i; end 4'b0000: begin $display("achieve node: 24,0,0,4"); tdo_mux_out = bs_chain_tdo_i; end 4'b1001: begin $display("achieve node: 24,0,0,5"); tdo_mux_out = mbist_tdo_i; end default: begin tdo_mux_out = bypassed_tdo; $display("achieve node: 24,0,0,6"); end endcase end end

always @(posedge s_clk_neg or negedge trstn_pad_i) begin $display("achieve node: 25,1");if (trstn_pad_i == 0) begin  $display("achieve node: 25,1,1");tdo_pad_o <= 1'b0; end  else begin  $display("achieve node: 25,1,0");tdo_pad_o <= tdo_mux_out; end  end

always @(posedge s_clk_neg or negedge trstn_pad_i) begin $display("achieve node: 26,1");if (trstn_pad_i == 0) begin  $display("achieve node: 26,1,1");tdo_padoe_o <= 1'b0; end  else begin  $display("achieve node: 26,1,0");tdo_padoe_o <= shift_ir | shift_dr; end  end

endmodule

