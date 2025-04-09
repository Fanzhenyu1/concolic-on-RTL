
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
input   tms_pad_i;      // JTAG test mode select pad
input   tck_pad_i;      // JTAG test clock pad
input   trstn_pad_i;     // JTAG test reset pad
input   tdi_pad_i;      // JTAG test data input pad
output  tdo_pad_o;      // JTAG test data output pad
output  tdo_padoe_o;    // Output enable for JTAG test data output pad 

input   test_mode_i;     // test mode input

// TAP states
output  test_logic_reset_o;
output  run_test_idle_o;
output  shift_dr_o;
output  pause_dr_o;
output  update_dr_o;
output  capture_dr_o;

// Select signals for boundary scan or mbist
output  extest_select_o;
output  sample_preload_select_o;
output  mbist_select_o;
output  debug_select_o;

// TDO signal that is connected to TDI of sub-modules.
output  tdi_o;

// TDI signals from sub-modules
input   debug_tdo_i;    // from debug module
input   bs_chain_tdo_i; // from Boundary Scan Chain
input   mbist_tdo_i;    // from Mbist Chain

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


reg [3:0] TAP_state;          // FIXED NOT POSSIBLE IN SYNTHESIS -->  = `STATE_test_logic_reset;  // current state of the TAP controller
reg [3:0] next_TAP_state;     // state TAP will take at next rising TCK, combinational signal
reg        passchk;
reg [31:0] correct;
reg [31:0] pass;
reg [4:0]  bitindex; 
// sequential part of the FSM
always @ (posedge tck_pad_i or negedge trstn_pad_i)
begin
	if(trstn_pad_i == 0) begin
		TAP_state = `STATE_test_logic_reset;
		pass = 32'hDEADBEEF;					//warning: 此处安全密钥是硬编码的，存在安全漏洞
	end
	else
		TAP_state = next_TAP_state;
end


// Determination of next state; purely combinatorial
always @ (TAP_state or tms_pad_i)
begin
	case(TAP_state)
		`STATE_test_logic_reset:
			begin
			passchk = 0;
			if(tms_pad_i) next_TAP_state = `STATE_test_logic_reset; 
			else next_TAP_state = `STATE_run_test_idle;
			end
		`STATE_run_test_idle:
			begin
				if(tms_pad_i && (passchk)) next_TAP_state = `STATE_select_dr_scan; 
				else begin
					next_TAP_state = `STATE_run_test_idle;
					if(correct >= 32'h0001_FFFF) passchk = 1;	//warning: 密码检查逻辑出错，检查位数过多			
					else if(tdi_o == pass[bitindex]) begin
						correct++;
						bitindex++;
					end				//warning:密码检查逻辑出错，非按位检查，无else分支
				end
			end
		`STATE_select_dr_scan:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_select_ir_scan; 
			else next_TAP_state = `STATE_capture_dr;
			end
		`STATE_capture_dr:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_exit1_dr; 
			else next_TAP_state = `STATE_shift_dr;
			end
		`STATE_shift_dr:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_exit1_dr; 
			else next_TAP_state = `STATE_shift_dr;
			end
		`STATE_exit1_dr:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_update_dr; 
			else next_TAP_state = `STATE_pause_dr;
			end
		`STATE_pause_dr:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_exit2_dr; 
			else next_TAP_state = `STATE_pause_dr;
			end
		`STATE_exit2_dr:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_update_dr; 
			else next_TAP_state = `STATE_shift_dr;
			end
		`STATE_update_dr:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_select_dr_scan; 
			else next_TAP_state = `STATE_run_test_idle;
			end
		`STATE_select_ir_scan:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_test_logic_reset;
			else next_TAP_state = `STATE_capture_ir;
			end
		`STATE_capture_ir:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_exit1_ir; 
			else next_TAP_state = `STATE_shift_ir;
			end
		`STATE_shift_ir:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_exit1_ir; 
			else next_TAP_state = `STATE_shift_ir;
			end
		`STATE_exit1_ir:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_update_ir;
			else next_TAP_state = `STATE_pause_ir;
			end
		`STATE_pause_ir:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_exit2_ir;
			else next_TAP_state = `STATE_pause_ir;
			end
		`STATE_exit2_ir:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_update_ir;
			else next_TAP_state = `STATE_shift_ir;
			end
		`STATE_update_ir:
			begin
			if(tms_pad_i) next_TAP_state = `STATE_select_dr_scan;
			else next_TAP_state = `STATE_run_test_idle;
			end
		default: next_TAP_state = `STATE_test_logic_reset;  // can't actually happen
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
		`STATE_test_logic_reset: test_logic_reset = 1'b1;
		`STATE_run_test_idle:    run_test_idle = 1'b1;
		`STATE_select_dr_scan:   select_dr_scan = 1'b1;
		`STATE_capture_dr:       capture_dr = 1'b1;
		`STATE_shift_dr:         shift_dr = 1'b1;
		`STATE_exit1_dr:         exit1_dr = 1'b1;
		`STATE_pause_dr:         pause_dr = 1'b1;
		`STATE_exit2_dr:         exit2_dr = 1'b1;
		`STATE_update_dr:        update_dr = 1'b1;
		`STATE_select_ir_scan:   select_ir_scan = 1'b1;
		`STATE_capture_ir:       capture_ir = 1'b1;
		`STATE_shift_ir:         shift_ir = 1'b1;
		`STATE_exit1_ir:         exit1_ir = 1'b1;
		`STATE_pause_ir:         pause_ir = 1'b1;
		`STATE_exit2_ir:         exit2_ir = 1'b1;
		`STATE_update_ir:        update_ir = 1'b1;
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
reg [`IR_LENGTH-1:0]  jtag_ir;          // Instruction register
reg [`IR_LENGTH-1:0]  latched_jtag_ir; //, latched_jtag_ir_neg;
wire                  instruction_tdo;

always @ (posedge tck_pad_i or negedge trstn_pad_i)
begin
  if(trstn_pad_i == 0)
    jtag_ir[`IR_LENGTH-1:0] <= `IR_LENGTH'b0;
  else if (test_logic_reset == 1)
	jtag_ir[`IR_LENGTH-1:0] <= `IR_LENGTH'b0;
  else if(capture_ir)
    jtag_ir <= 4'b0101;          // This value is fixed for easier fault detection
  else if(shift_ir)
    jtag_ir[`IR_LENGTH-1:0] <= {tdi_pad_i, jtag_ir[`IR_LENGTH-1:1]};
end

assign instruction_tdo = jtag_ir[0];  // This is latched on a negative TCK edge after the output MUX

// Updating jtag_ir (Instruction Register)
// jtag_ir should be latched on FALLING EDGE of TCK when capture_ir == 1
always @ (posedge s_clk_neg or negedge trstn_pad_i)
begin
  if(trstn_pad_i == 0)
    latched_jtag_ir <= `IDCODE;   // IDCODE selected after reset
  else if (test_logic_reset)
    latched_jtag_ir <= `IDCODE;   // IDCODE selected after reset
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
    idcode_reg <= `IDCODE_VALUE;   // IDCODE selected after reset
  else if (test_logic_reset)
    idcode_reg <= `IDCODE_VALUE;   // IDCODE selected after reset
  else if(idcode_select & capture_dr)
    idcode_reg <=  `IDCODE_VALUE;
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
    `EXTEST:            extest_select           = 1'b1;    // External test
    `SAMPLE_PRELOAD:    sample_preload_select   = 1'b1;    // Sample preload
    `IDCODE:            idcode_select           = 1'b1;    // ID Code
    `MBIST:             mbist_select            = 1'b1;    // Mbist test
    `DEBUG:             debug_select            = 1'b1;    // Debug
    `BYPASS:            bypass_select           = 1'b1;    // BYPASS
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
        `IDCODE:            tdo_mux_out = idcode_tdo;       // Reading ID code
        `DEBUG:             tdo_mux_out = debug_tdo_i;      // Debug
        `SAMPLE_PRELOAD:    tdo_mux_out = bs_chain_tdo_i;   // Sampling/Preloading
        `EXTEST:            tdo_mux_out = bs_chain_tdo_i;   // External test
        `MBIST:             tdo_mux_out = mbist_tdo_i;      // Mbist test
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
