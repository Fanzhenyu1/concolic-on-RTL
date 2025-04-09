
`include "adbg_tap_defines.v"

// Top module
module adbg_tap_top(
                // JTAG pads
                tms_pad_i, 
                tck_pad_i, 
                trstn_pad_i, 
                tdi_pad_i, 
                tdo_pad_o, 
                tdo_padoe_o,

                test_mode_i,

                // TAP states
				test_logic_reset_o,
				run_test_idle_o,
                shift_dr_o,
                pause_dr_o, 
                update_dr_o,
                capture_dr_o,
                
                // Select signals for boundary scan or mbist
                extest_select_o, 
                sample_preload_select_o,
                mbist_select_o,
                debug_select_o,
                
                // TDO signal that is connected to TDI of sub-modules.
                tdi_o, 
                
                // TDI signals from sub-modules
                debug_tdo_i,    // from debug module
                bs_chain_tdo_i, // from Boundary Scan Chain
                mbist_tdo_i     // from Mbist Chain
              );


// JTAG pins
input wire   tms_pad_i;      // JTAG test mode select pad
input wire   tck_pad_i;      // JTAG test clock pad
input wire   trstn_pad_i;     // JTAG test reset pad
input wire   tdi_pad_i;      // JTAG test data input wire pad
output reg  tdo_pad_o;      // JTAG test data output reg pad
output reg  tdo_padoe_o;    // Output enable for JTAG test data output reg pad 

input wire   test_mode_i;     // test mode input

// TAP states
output wire  test_logic_reset_o;
output wire  run_test_idle_o;
output wire  shift_dr_o;
output wire  pause_dr_o;
output wire  update_dr_o;
output wire  capture_dr_o;

// Select signals for boundary scan or mbist
output wire  extest_select_o;
output wire  sample_preload_select_o;
output wire  mbist_select_o;
output wire  debug_select_o;

// TDO signal that is connected to TDI of sub-modules.
output reg  tdi_o;

// TDI signals from sub-modules
input wire   debug_tdo_i;    // from debug module
input wire   bs_chain_tdo_i; // from Boundary Scan Chain
input wire   mbist_tdo_i;    // from Mbist Chain

// Wires which depend on the state of the TAP FSM
reg     test_logic_reset;
reg     run_test_idle;
reg     select_dr_scan;
reg     capture_dr;
reg     shift_dr;
reg     exit1_dr;
reg     pause_dr;
reg     exit2_dr;
reg     update_dr;
reg     select_ir_scan;
reg     capture_ir;
reg     shift_ir;
reg     exit1_ir;
reg     pause_ir;
reg     exit2_ir;
reg     update_ir;

// Wires which depend on the current value in the IR
reg     extest_select;
reg     sample_preload_select;
reg     idcode_select;
reg     mbist_select;
reg     debug_select;
reg     bypass_select;

// TDO and enable
reg     tdo_pad_o;
reg     tdo_padoe_o;

wire    s_clk_neg;
wire    s_tck_inv;

// cluster_clock_inverter u_clk_inv (.clk_i(tck_pad_i), .clk_o(s_tck_inv));
assign s_tck_inv = ~tck_pad_i;
// cluster_clock_mux2 u_clk_mux(
//     .clk0_i(s_tck_inv),
//     .clk1_i(tck_pad_i),
//     .clk_sel_i(test_mode_i),
//     .clk_o(s_clk_neg)
// );
always @ (*) begin
	if(test_mode_i) begin
		s_clk_neg = tck_pad_i;
	end else begin
		s_clk_neg = s_tck_inv;
	end
end

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


/**********************************************************************************
*                                                                                 *
*   TAP State Machine: Fully JTAG compliant                                       *
*                                                                                 *
**********************************************************************************/
// Definition of machine state values.  We could one-hot encode this, and use 16
// registers, but this uses binary encoding for the minimum of 4 DFF's instead.


reg [3:0] TAP_state;          // FIXED NOT POSSIBLE IN SYNTHESIS -->  = 4'hF;  // current state of the TAP controller
reg [3:0] next_TAP_state;     // state TAP will take at next rising TCK, combinational signal
reg        passchk;
reg [31:0] correct;
reg [31:0] pass;
reg [4:0]  bitindex; 
// sequential part of the FSM
always @ (posedge tck_pad_i or negedge trstn_pad_i)
begin
	if(trstn_pad_i == 0) begin
		TAP_state = 4'hF;
		pass = 32'hDEADBEEF;					//warning: 此处安全密钥是硬编码的，存在安全漏洞
	end
	else
		TAP_state = next_TAP_state;
end


// Determination of next state; purely combinatorial
always @ (TAP_state or tms_pad_i)
begin
	case(TAP_state)
		4'hF:
			begin
			passchk = 0;
			if(tms_pad_i) next_TAP_state = 4'hF; 
			else next_TAP_state = 4'hC;
			end
		4'hC:
			begin
				if(tms_pad_i && (passchk)) next_TAP_state = 4'h7; 
				else begin
					next_TAP_state = 4'hC;
					if(correct >= 32'h0001_FFFF) passchk = 1;	//warning: 密码检查逻辑出错，检查位数过多			
					else if(tdi_o == pass[bitindex]) begin
						correct++;
						bitindex++;
					end				//warning:密码检查逻辑出错，非按位检查，无else分支
				end
			end
		4'h7:
			begin
			if(tms_pad_i) next_TAP_state = 4'h4; 
			else next_TAP_state = 4'h6;
			end
		4'h6:
			begin
			if(tms_pad_i) next_TAP_state = 4'h1; 
			else next_TAP_state = 4'h2;
			end
		4'h2:
			begin
			if(tms_pad_i) next_TAP_state = 4'h1; 
			else next_TAP_state = 4'h2;
			end
		4'h1:
			begin
			if(tms_pad_i) next_TAP_state = 4'h5; 
			else next_TAP_state = 4'h3;
			end
		4'h3:
			begin
			if(tms_pad_i) next_TAP_state = 4'h0; 
			else next_TAP_state = 4'h3;
			end
		4'h0:
			begin
			if(tms_pad_i) next_TAP_state = 4'h5; 
			else next_TAP_state = 4'h2;
			end
		4'h5:
			begin
			if(tms_pad_i) next_TAP_state = 4'h7; 
			else next_TAP_state = 4'hC;
			end
		4'h4:
			begin
			if(tms_pad_i) next_TAP_state = 4'hF;
			else next_TAP_state = 4'hE;
			end
		4'hE:
			begin
			if(tms_pad_i) next_TAP_state = 4'h9; 
			else next_TAP_state = 4'hA;
			end
		4'hA:
			begin
			if(tms_pad_i) next_TAP_state = 4'h9; 
			else next_TAP_state = 4'hA;
			end
		4'h9:
			begin
			if(tms_pad_i) next_TAP_state = 4'hD;
			else next_TAP_state = 4'hB;
			end
		4'hB:
			begin
			if(tms_pad_i) next_TAP_state = 4'h8;
			else next_TAP_state = 4'hB;
			end
		4'h8:
			begin
			if(tms_pad_i) next_TAP_state = 4'hD;
			else next_TAP_state = 4'hA;
			end
		4'hD:
			begin
			if(tms_pad_i) next_TAP_state = 4'h7;
			else next_TAP_state = 4'hC;
			end
		default: next_TAP_state = 4'hF;  // can't actually happen
	endcase
end


// Outputs of state machine, pure combinatorial
always @ (TAP_state)
begin
	// Default everything to 0, keeps the case statement simple
	test_logic_reset = 1'b0;
	run_test_idle = 1'b0;
	select_dr_scan = 1'b0;
	capture_dr = 1'b0;
	shift_dr = 1'b0;
	exit1_dr = 1'b0;
	pause_dr = 1'b0;
	exit2_dr = 1'b0;
	update_dr = 1'b0;
	select_ir_scan = 1'b0;
	capture_ir = 1'b0;
	shift_ir = 1'b0;
	exit1_ir = 1'b0;
	pause_ir = 1'b0;
	exit2_ir = 1'b0;
	update_ir = 1'b0;

	case(TAP_state)
		4'hF: test_logic_reset = 1'b1;
		4'hC:    run_test_idle = 1'b1;
		4'h7:   select_dr_scan = 1'b1;
		4'h6:       capture_dr = 1'b1;
		4'h2:         shift_dr = 1'b1;
		4'h1:         exit1_dr = 1'b1;
		4'h3:         pause_dr = 1'b1;
		4'h0:         exit2_dr = 1'b1;
		4'h5:        update_dr = 1'b1;
		4'h4:   select_ir_scan = 1'b1;
		4'hE:       capture_ir = 1'b1;
		4'hA:         shift_ir = 1'b1;
		4'h9:         exit1_ir = 1'b1;
		4'hB:         pause_ir = 1'b1;
		4'h8:         exit2_ir = 1'b1;
		4'hD:        update_ir = 1'b1;
		default: ;
	endcase
end

/**********************************************************************************
*                                                                                 *
*   End: TAP State Machine                                                        *
*                                                                                 *
**********************************************************************************/



/**********************************************************************************
*                                                                                 *
*   jtag_ir:  JTAG Instruction Register                                           *
*                                                                                 *
**********************************************************************************/
reg [4-1:0]  jtag_ir;          // Instruction register
reg [4-1:0]  latched_jtag_ir; //, latched_jtag_ir_neg;
wire                  instruction_tdo;

always @ (posedge tck_pad_i or negedge trstn_pad_i)
begin
  if(trstn_pad_i == 0)
    jtag_ir[4-1:0] <= 4'b0;
  else if (test_logic_reset == 1)
	jtag_ir[4-1:0] <= 4'b0;
  else if(capture_ir)
    jtag_ir <= 4'b0101;          // This value is fixed for easier fault detection
  else if(shift_ir)
    jtag_ir[4-1:0] <= {tdi_pad_i, jtag_ir[4-1:1]};
end

assign instruction_tdo = jtag_ir[0];  // This is latched on a negative TCK edge after the output MUX

// Updating jtag_ir (Instruction Register)
// jtag_ir should be latched on FALLING EDGE of TCK when capture_ir == 1
always @ (posedge s_clk_neg or negedge trstn_pad_i)
begin
  if(trstn_pad_i == 0)
    latched_jtag_ir <= 4'b0010;   // IDCODE selected after reset
  else if (test_logic_reset)
    latched_jtag_ir <= 4'b0010;   // IDCODE selected after reset
  else if(update_ir)
    latched_jtag_ir <= jtag_ir;
end

/**********************************************************************************
*                                                                                 *
*   End: jtag_ir                                                                  *
*                                                                                 *
**********************************************************************************/



/**********************************************************************************
*                                                                                 *
*   idcode logic                                                                  *
*                                                                                 *
**********************************************************************************/
reg [31:0] idcode_reg;
wire        idcode_tdo;

always @ (posedge tck_pad_i or negedge trstn_pad_i)
begin
  if(trstn_pad_i == 0)
    idcode_reg <= 32'h249511c3;   // IDCODE selected after reset
  else if (test_logic_reset)
    idcode_reg <= 32'h249511c3;   // IDCODE selected after reset
  else if(idcode_select & capture_dr)
    idcode_reg <=  32'h249511c3;
  else if(idcode_select & shift_dr)
    idcode_reg <=  {tdi_pad_i, idcode_reg[31:1]};

end

assign idcode_tdo = idcode_reg[0];   // This is latched on a negative TCK edge after the output MUX

/**********************************************************************************
*                                                                                 *
*   End: idcode logic                                                             *
*                                                                                 *
**********************************************************************************/


/**********************************************************************************
*                                                                                 *
*   Bypass logic                                                                  *
*                                                                                 *
**********************************************************************************/
wire  bypassed_tdo;
reg   bypass_reg;  // This is a 1-bit register

always @ (posedge tck_pad_i or negedge trstn_pad_i)
begin
  if (trstn_pad_i == 0)
     bypass_reg <=  1'b0;
  else if (test_logic_reset == 1)
     bypass_reg <=  1'b0;
  else if (bypass_select & capture_dr)
    bypass_reg<= 1'b0;
  else if(bypass_select & shift_dr)
    bypass_reg<= tdi_pad_i;
end

assign bypassed_tdo = bypass_reg;   // This is latched on a negative TCK edge after the output MUX

/**********************************************************************************
*                                                                                 *
*   End: Bypass logic                                                             *
*                                                                                 *
**********************************************************************************/


/**********************************************************************************
*                                                                                 *
*   Selecting active data register                                                *
*                                                                                 *
**********************************************************************************/
always @ (latched_jtag_ir)
begin
  extest_select           = 1'b0;
  sample_preload_select   = 1'b0;
  idcode_select           = 1'b0;
  mbist_select            = 1'b0;
  debug_select            = 1'b0;
  bypass_select           = 1'b0;

  case(latched_jtag_ir)    /* synthesis parallel_case */ 
    4'b0000:            extest_select           = 1'b1;    // External test
    4'b0001:    sample_preload_select   = 1'b1;    // Sample preload
    4'b0010:            idcode_select           = 1'b1;    // ID Code
    4'b1001:             mbist_select            = 1'b1;    // Mbist test
    4'b1000:             debug_select            = 1'b1;    // Debug
    4'b1111:            bypass_select           = 1'b1;    // BYPASS
    default:            bypass_select           = 1'b1;    // BYPASS
  endcase
end


/**********************************************************************************
*                                                                                 *
*   Multiplexing TDO data                                                         *
*                                                                                 *
**********************************************************************************/
reg tdo_mux_out;  // really just a wire

always @ (shift_ir or instruction_tdo or latched_jtag_ir or idcode_tdo or
          debug_tdo_i or bs_chain_tdo_i or mbist_tdo_i or bypassed_tdo or
			bs_chain_tdo_i)
begin
  if(shift_ir)
    tdo_mux_out = instruction_tdo;
  else
    begin
      case(latched_jtag_ir)    // synthesis parallel_case
        4'b0010:            tdo_mux_out = idcode_tdo;       // Reading ID code
        4'b1000:             tdo_mux_out = debug_tdo_i;      // Debug
        4'b0001:    tdo_mux_out = bs_chain_tdo_i;   // Sampling/Preloading
        4'b0000:            tdo_mux_out = bs_chain_tdo_i;   // External test
        4'b1001:             tdo_mux_out = mbist_tdo_i;      // Mbist test
        default:            tdo_mux_out = bypassed_tdo;     // BYPASS instruction
      endcase
    end
end


// TDO changes state at negative edge of TCK
always @ (posedge s_clk_neg or negedge trstn_pad_i)
begin
  if (trstn_pad_i == 0)
    tdo_pad_o <= 1'b0;
  else
    tdo_pad_o <= tdo_mux_out;
end


// Tristate control for tdo_pad_o pin
always @ (posedge s_clk_neg or negedge trstn_pad_i)
begin
  if (trstn_pad_i == 0)
    tdo_padoe_o <= 1'b0;
  else
    tdo_padoe_o <= shift_ir | shift_dr;
end
/**********************************************************************************
*                                                                                 *
*   End: Multiplexing TDO data                                                    *
*                                                                                 *
**********************************************************************************/

endmodule
