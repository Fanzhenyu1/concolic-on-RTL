module usb_phy (    clk,    rst,    phy_tx_mode,    usb_rst,    txdp,    txdn,    txoe,    rxd,    rxdp,    rxdn,    DataOut_i,    TxValid_i,    TxReady_o,    RxValid_o,    RxActive_o,    RxError_o,    DataIn_o,    LineState_o);

 input wire clk;

 input wire rst;

 input wire phy_tx_mode;

 output reg usb_rst;

 output reg txdp;

 output reg txdn;

 output reg txoe;

 input wire rxd;

 input wire rxdp;

 input wire rxdn;

 input wire [7:0] DataOut_i;

 input wire TxValid_i;

 output reg TxReady_o;

 output wire RxValid_o;

 output wire RxActive_o;

 output wire RxError_o;

 output wire [7:0] DataIn_o;

 output wire [1:0] LineState_o;

 reg [4:0] rst_cnt;



 reg i_tx_phy_TxReady_o;

 reg [2:0] i_tx_phy_state;

 reg [2:0] i_tx_phy_next_state;

 reg i_tx_phy_tx_ready_d;

 reg i_tx_phy_ld_sop_d;

 reg i_tx_phy_ld_data_d;

 reg i_tx_phy_ld_eop_d;

 reg i_tx_phy_tx_ip;

 reg i_tx_phy_tx_ip_sync;

 reg [2:0] i_tx_phy_bit_cnt;

 reg [7:0] i_tx_phy_hold_reg;

 reg [7:0] i_tx_phy_hold_reg_d;

 reg i_tx_phy_sd_raw_o;

 reg i_tx_phy_data_done;

 reg i_tx_phy_sft_done;

 reg i_tx_phy_sft_done_r;

 reg i_tx_phy_ld_data;

 reg [2:0] i_tx_phy_one_cnt;

 wire i_tx_phy_stuff;

 reg i_tx_phy_sd_bs_o;

 reg i_tx_phy_sd_nrzi_o;

 reg i_tx_phy_append_eop;

 reg i_tx_phy_append_eop_sync1;

 reg i_tx_phy_append_eop_sync2;

 reg i_tx_phy_append_eop_sync3;

 reg i_tx_phy_append_eop_sync4;

 reg i_tx_phy_txdp;

 reg i_tx_phy_txdn;

 reg i_tx_phy_txoe_r1;

 reg i_tx_phy_txoe_r2;

 reg i_tx_phy_txoe;

 reg i_rx_phy_rxd_s0;

 reg i_rx_phy_rxd_s1;

 reg i_rx_phy_rxd_s;

 reg i_rx_phy_rxdp_s0;

 reg i_rx_phy_rxdp_s1;

 reg i_rx_phy_rxdp_s;

 reg i_rx_phy_rxdp_s_r;

 reg i_rx_phy_rxdn_s0;

 reg i_rx_phy_rxdn_s1;

 reg i_rx_phy_rxdn_s;

 reg i_rx_phy_rxdn_s_r;

 reg i_rx_phy_synced_d;

 reg i_rx_phy_rxd_r;

 reg i_rx_phy_rx_en;

 reg i_rx_phy_rx_active;

 reg [2:0] i_rx_phy_bit_cnt;

 reg i_rx_phy_rx_valid1;

 reg i_rx_phy_rx_valid;

 reg i_rx_phy_shift_en;

 reg i_rx_phy_sd_r;

 reg i_rx_phy_sd_nrzi;

 reg [7:0] i_rx_phy_hold_reg;

 reg [2:0] i_rx_phy_one_cnt;

 reg [1:0] i_rx_phy_dpll_state;

 reg [1:0] i_rx_phy_dpll_next_state;

 reg i_rx_phy_fs_ce_d;

 reg i_rx_phy_fs_ce;

 reg [2:0] i_rx_phy_fs_state;

 reg [2:0] i_rx_phy_fs_next_state;

 reg i_rx_phy_rx_valid_r;

 reg i_rx_phy_sync_err_d;

 reg i_rx_phy_sync_err;

 reg i_rx_phy_bit_stuff_err;

 reg i_rx_phy_se0_r;

 reg i_rx_phy_byte_err;

 reg i_rx_phy_se0_s;

 reg i_rx_phy_fs_ce_r1;

 reg i_rx_phy_fs_ce_r2;

always @(posedge clk or negedge rst) begin $display("achieve node: 0,1"); if (!(rst)) begin $display("achieve node: 0,1,1"); rst_cnt <= 5'h0; end else begin $display("achieve node: 0,1,0");  if (LineState_o != 2'h0) begin $display("achieve node: 0,1,0,1"); rst_cnt <= 5'h0; end else begin $display("achieve node: 0,1,0,0");  if (!(usb_rst) && i_rx_phy_fs_ce) begin $display("achieve node: 0,1,0,0,1"); rst_cnt <= (rst_cnt + 5'h1); end end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 1,1"); if (!(rst)) begin $display("achieve node: 1,1,1"); usb_rst <= 1'b0; end else begin $display("achieve node: 1,1,0");  usb_rst <= (rst_cnt == 5'h1f); end end

 assign txdp = i_tx_phy_txdp;

 assign txdn = i_tx_phy_txdn;

 assign txoe = i_tx_phy_txoe;

 assign TxReady_o = i_tx_phy_TxReady_o;

always @(posedge clk or negedge rst) begin $display("achieve node: 6,1"); if (!(rst)) begin $display("achieve node: 6,1,1"); i_tx_phy_TxReady_o <= 1'b0; end else begin $display("achieve node: 6,1,0");  i_tx_phy_TxReady_o <= (i_tx_phy_tx_ready_d & TxValid_i); end end

always @(posedge clk) begin $display("achieve node: 7,1"); i_tx_phy_ld_data <= i_tx_phy_ld_data_d; end

always @(posedge clk or negedge rst) begin $display("achieve node: 8,1"); if (!(rst)) begin $display("achieve node: 8,1,1"); i_tx_phy_tx_ip <= 1'b0; end else begin $display("achieve node: 8,1,0");  if (i_tx_phy_ld_sop_d) begin $display("achieve node: 8,1,0,1"); i_tx_phy_tx_ip <= 1'b1; end else begin $display("achieve node: 8,1,0,0");  if (i_tx_phy_append_eop_sync3) begin $display("achieve node: 8,1,0,0,1"); i_tx_phy_tx_ip <= 1'b0; end end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 9,1"); if (!(rst)) begin $display("achieve node: 9,1,1"); i_tx_phy_tx_ip_sync <= 1'b0; end else begin $display("achieve node: 9,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 9,1,0,1"); i_tx_phy_tx_ip_sync <= i_tx_phy_tx_ip; end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 10,1"); if (!(rst)) begin $display("achieve node: 10,1,1"); i_tx_phy_data_done <= 1'b0; end else begin $display("achieve node: 10,1,0");  if (TxValid_i && !(i_tx_phy_tx_ip)) begin $display("achieve node: 10,1,0,1"); i_tx_phy_data_done <= 1'b1; end else begin $display("achieve node: 10,1,0,0");  if (!(TxValid_i)) begin $display("achieve node: 10,1,0,0,1"); i_tx_phy_data_done <= 1'b0; end end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 11,1"); if (!(rst)) begin $display("achieve node: 11,1,1"); i_tx_phy_bit_cnt <= 3'h0; end else begin $display("achieve node: 11,1,0");  if (!(i_tx_phy_tx_ip_sync)) begin $display("achieve node: 11,1,0,1"); i_tx_phy_bit_cnt <= 3'h0; end else begin $display("achieve node: 11,1,0,0");  if (i_rx_phy_fs_ce && !(i_tx_phy_stuff)) begin $display("achieve node: 11,1,0,0,1"); i_tx_phy_bit_cnt <= (i_tx_phy_bit_cnt + 3'h1); end end end end

always @(posedge clk) begin $display("achieve node: 12,1"); if (!(i_tx_phy_tx_ip_sync)) begin $display("achieve node: 12,1,1"); i_tx_phy_sd_raw_o <= 1'b0; end else begin $display("achieve node: 12,1,0");  case (i_tx_phy_bit_cnt) 3'h0: begin  i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[0]; $display("achieve node: 12,1,0,1");  end 3'h1: begin  i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[1]; $display("achieve node: 12,1,0,2");  end 3'h2: begin  i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[2]; $display("achieve node: 12,1,0,3");  end 3'h3: begin  i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[3]; $display("achieve node: 12,1,0,4");  end 3'h4: begin  i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[4]; $display("achieve node: 12,1,0,5");  end 3'h5: begin  i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[5]; $display("achieve node: 12,1,0,6");  end 3'h6: begin  i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[6]; $display("achieve node: 12,1,0,7");  end 3'h7: begin  i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[7]; $display("achieve node: 12,1,0,8");  end endcase end end

always @(posedge clk) begin $display("achieve node: 13,1"); i_tx_phy_sft_done <= (!((i_tx_phy_one_cnt == 3'h6)) & (i_tx_phy_bit_cnt == 3'h7)); end

always @(posedge clk) begin $display("achieve node: 14,1"); i_tx_phy_sft_done_r <= i_tx_phy_sft_done; end

always @(posedge clk) begin $display("achieve node: 15,1"); if (i_tx_phy_ld_sop_d) begin $display("achieve node: 15,1,1"); i_tx_phy_hold_reg <= 8'h80; end else begin $display("achieve node: 15,1,0");  if (i_tx_phy_ld_data) begin $display("achieve node: 15,1,0,1"); i_tx_phy_hold_reg <= DataOut_i; end end end

always @(posedge clk) begin $display("achieve node: 16,1"); i_tx_phy_hold_reg_d <= i_tx_phy_hold_reg; end

always @(posedge clk or negedge rst) begin $display("achieve node: 17,1"); if (!(rst)) begin $display("achieve node: 17,1,1"); i_tx_phy_one_cnt <= 3'h0; end else begin $display("achieve node: 17,1,0");  if (!(i_tx_phy_tx_ip_sync)) begin $display("achieve node: 17,1,0,1"); i_tx_phy_one_cnt <= 3'h0; end else begin $display("achieve node: 17,1,0,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 17,1,0,0,1"); if (!(i_tx_phy_sd_raw_o) || (i_tx_phy_one_cnt == 3'h6)) begin $display("achieve node: 17,1,0,0,1,1"); i_tx_phy_one_cnt <= 3'h0; end else begin $display("achieve node: 17,1,0,0,1,0");  i_tx_phy_one_cnt <= (i_tx_phy_one_cnt + 3'h1); end end end end end

 assign i_tx_phy_stuff = (i_tx_phy_one_cnt == 3'h6);

always @(posedge clk or negedge rst) begin $display("achieve node: 19,1"); if (!(rst)) begin $display("achieve node: 19,1,1"); i_tx_phy_sd_bs_o <= 1'h0; end else begin $display("achieve node: 19,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 19,1,0,1"); i_tx_phy_sd_bs_o <= ( ( !( i_tx_phy_tx_ip_sync) ) ? ( 1'b0 ) : ( ( ( ( i_tx_phy_one_cnt == 3'h6 ) ) ? ( 1'b0 ) : ( i_tx_phy_sd_raw_o ) ) ) ); end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 20,1"); if (!(rst)) begin $display("achieve node: 20,1,1"); i_tx_phy_sd_nrzi_o <= 1'b1; end else begin $display("achieve node: 20,1,0");  if (!(i_tx_phy_tx_ip_sync) || !(i_tx_phy_txoe_r1)) begin $display("achieve node: 20,1,0,1"); i_tx_phy_sd_nrzi_o <= 1'b1; end else begin $display("achieve node: 20,1,0,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 20,1,0,0,1"); i_tx_phy_sd_nrzi_o <= ( ( i_tx_phy_sd_bs_o ) ? ( i_tx_phy_sd_nrzi_o ) : ( ~( i_tx_phy_sd_nrzi_o) ) ); end end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 21,1"); if (!(rst)) begin $display("achieve node: 21,1,1"); i_tx_phy_append_eop <= 1'b0; end else begin $display("achieve node: 21,1,0");  if (i_tx_phy_ld_eop_d) begin $display("achieve node: 21,1,0,1"); i_tx_phy_append_eop <= 1'b1; end else begin $display("achieve node: 21,1,0,0");  if (i_tx_phy_append_eop_sync2) begin $display("achieve node: 21,1,0,0,1"); i_tx_phy_append_eop <= 1'b0; end end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 22,1"); if (!(rst)) begin $display("achieve node: 22,1,1"); i_tx_phy_append_eop_sync1 <= 1'b0; end else begin $display("achieve node: 22,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 22,1,0,1"); i_tx_phy_append_eop_sync1 <= i_tx_phy_append_eop; end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 23,1"); if (!(rst)) begin $display("achieve node: 23,1,1"); i_tx_phy_append_eop_sync2 <= 1'b0; end else begin $display("achieve node: 23,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 23,1,0,1"); i_tx_phy_append_eop_sync2 <= i_tx_phy_append_eop_sync1; end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 24,1"); if (!(rst)) begin $display("achieve node: 24,1,1"); i_tx_phy_append_eop_sync3 <= 1'b0; end else begin $display("achieve node: 24,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 24,1,0,1"); i_tx_phy_append_eop_sync3 <= ( i_tx_phy_append_eop_sync2 | ( i_tx_phy_append_eop_sync3 & !( i_tx_phy_append_eop_sync4) ) ); end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 25,1"); if (!(rst)) begin $display("achieve node: 25,1,1"); i_tx_phy_append_eop_sync4 <= 1'b0; end else begin $display("achieve node: 25,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 25,1,0,1"); i_tx_phy_append_eop_sync4 <= i_tx_phy_append_eop_sync3; end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 26,1"); if (!(rst)) begin $display("achieve node: 26,1,1"); i_tx_phy_txoe_r1 <= 1'b0; end else begin $display("achieve node: 26,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 26,1,0,1"); i_tx_phy_txoe_r1 <= i_tx_phy_tx_ip_sync; end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 27,1"); if (!(rst)) begin $display("achieve node: 27,1,1"); i_tx_phy_txoe_r2 <= 1'b0; end else begin $display("achieve node: 27,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 27,1,0,1"); i_tx_phy_txoe_r2 <= i_tx_phy_txoe_r1; end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 28,1"); if (!(rst)) begin $display("achieve node: 28,1,1"); i_tx_phy_txoe <= 1'b1; end else begin $display("achieve node: 28,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 28,1,0,1"); i_tx_phy_txoe <= !((i_tx_phy_txoe_r1 | i_tx_phy_txoe_r2)); end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 29,1"); if (!(rst)) begin $display("achieve node: 29,1,1"); i_tx_phy_txdp <= 1'b1; end else begin $display("achieve node: 29,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 29,1,0,1"); i_tx_phy_txdp <= ( ( phy_tx_mode ) ? ( ( !( i_tx_phy_append_eop_sync3) & i_tx_phy_sd_nrzi_o ) ) : ( i_tx_phy_sd_nrzi_o ) ); end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 30,1"); if (!(rst)) begin $display("achieve node: 30,1,1"); i_tx_phy_txdn <= 1'b0; end else begin $display("achieve node: 30,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 30,1,0,1"); i_tx_phy_txdn <= ( ( phy_tx_mode ) ? ( ( !( i_tx_phy_append_eop_sync3) & ~( i_tx_phy_sd_nrzi_o) ) ) : ( i_tx_phy_append_eop_sync3 ) ); end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 31,1"); if (!(rst)) begin $display("achieve node: 31,1,1"); i_tx_phy_state <= 3'd0; end else begin $display("achieve node: 31,1,0");  i_tx_phy_state <= i_tx_phy_next_state; end end

always @ ( i_tx_phy_state or TxValid_i or i_tx_phy_data_done or ( i_tx_phy_sft_done & !( i_tx_phy_sft_done_r) ) or i_tx_phy_append_eop_sync3 or i_rx_phy_fs_ce) begin 
    i_tx_phy_next_state = i_tx_phy_state; i_tx_phy_tx_ready_d = 1'b0; i_tx_phy_ld_sop_d = 1'b0; i_tx_phy_ld_data_d = 1'b0; i_tx_phy_ld_eop_d = 1'b0; 
    case (i_tx_phy_state) 
    3'd0: begin  if (TxValid_i) begin $display("achieve node: 32,0,1");  $display("achieve node: 32,0,1,1"); i_tx_phy_ld_sop_d = 1'b1; i_tx_phy_next_state = 3'h1; end end 
    3'h1: begin  if (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)) begin $display("achieve node: 32,0,2");  $display("achieve node: 32,0,2,1"); i_tx_phy_tx_ready_d = 1'b1; i_tx_phy_ld_data_d = 1'b1; i_tx_phy_next_state = 3'h2; end end 
    3'h2: begin  if (!(i_tx_phy_data_done) && (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r))) begin $display("achieve node: 32,0,3");  $display("achieve node: 32,0,3,1"); i_tx_phy_ld_eop_d = 1'b1; i_tx_phy_next_state = 3'h3; end if (i_tx_phy_data_done && (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r))) begin $display("achieve node: 32,0,3,1,1"); i_tx_phy_tx_ready_d = 1'b1; i_tx_phy_ld_data_d = 1'b1; end end 
    3'h3: begin  if (i_tx_phy_append_eop_sync3) begin $display("achieve node: 32,0,4");  i_tx_phy_next_state = 3'h4; end end 3'h4: begin  if (!(i_tx_phy_append_eop_sync3) && i_rx_phy_fs_ce) begin $display("achieve node: 32,0,5");  i_tx_phy_next_state = 3'h5; end end 3'h5: begin  if (i_rx_phy_fs_ce) begin $display("achieve node: 32,0,6");  $display("achieve node: 32,0,6,1"); i_tx_phy_next_state = 3'd0; end end endcase end

 assign DataIn_o = i_rx_phy_hold_reg;

 assign RxValid_o = i_rx_phy_rx_valid;

 assign RxActive_o = i_rx_phy_rx_active;

 assign RxError_o = ((i_rx_phy_sync_err | i_rx_phy_bit_stuff_err) | i_rx_phy_byte_err);

 assign LineState_o = {i_rx_phy_rxdn_s1, i_rx_phy_rxdp_s1};

always @(posedge clk) begin $display("achieve node: 38,1"); i_rx_phy_rx_en <= txoe; end

always @(posedge clk) begin $display("achieve node: 39,1"); i_rx_phy_sync_err <= (!(i_rx_phy_rx_active) & i_rx_phy_sync_err_d); end

always @(posedge clk) begin $display("achieve node: 40,1"); i_rx_phy_rxd_s0 <= rxd; end

always @(posedge clk) begin $display("achieve node: 41,1"); i_rx_phy_rxd_s1 <= i_rx_phy_rxd_s0; end

always @(posedge clk) begin $display("achieve node: 42,1"); if (i_rx_phy_rxd_s0 && i_rx_phy_rxd_s1) begin $display("achieve node: 42,1,1"); i_rx_phy_rxd_s <= 1'b1; end else begin $display("achieve node: 42,1,0");  if (!(i_rx_phy_rxd_s0) && !(i_rx_phy_rxd_s1)) begin $display("achieve node: 42,1,0,1"); i_rx_phy_rxd_s <= 1'b0; end end end

always @(posedge clk) begin $display("achieve node: 43,1"); i_rx_phy_rxdp_s0 <= rxdp; end

always @(posedge clk) begin $display("achieve node: 44,1"); i_rx_phy_rxdp_s1 <= i_rx_phy_rxdp_s0; end

always @(posedge clk) begin $display("achieve node: 45,1"); i_rx_phy_rxdp_s_r <= (i_rx_phy_rxdp_s0 & i_rx_phy_rxdp_s1); end

always @(posedge clk) begin $display("achieve node: 46,1"); i_rx_phy_rxdp_s <= ((i_rx_phy_rxdp_s0 & i_rx_phy_rxdp_s1) | i_rx_phy_rxdp_s_r); end

always @(posedge clk) begin $display("achieve node: 47,1"); i_rx_phy_rxdn_s0 <= rxdn; end

always @(posedge clk) begin $display("achieve node: 48,1"); i_rx_phy_rxdn_s1 <= i_rx_phy_rxdn_s0; end

always @(posedge clk) begin $display("achieve node: 49,1"); i_rx_phy_rxdn_s_r <= (i_rx_phy_rxdn_s0 & i_rx_phy_rxdn_s1); end

always @(posedge clk) begin $display("achieve node: 50,1"); i_rx_phy_rxdn_s <= ((i_rx_phy_rxdn_s0 & i_rx_phy_rxdn_s1) | i_rx_phy_rxdn_s_r); end

always @(posedge clk) begin $display("achieve node: 51,1"); if (i_rx_phy_fs_ce) begin $display("achieve node: 51,1,1"); i_rx_phy_se0_s <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s)); end end

always @(posedge clk) begin $display("achieve node: 52,1"); i_rx_phy_rxd_r <= i_rx_phy_rxd_s; end

always @(posedge clk or negedge rst) begin $display("achieve node: 53,1"); if (!(rst)) begin $display("achieve node: 53,1,1"); i_rx_phy_dpll_state <= 2'h1; end else begin $display("achieve node: 53,1,0");  i_rx_phy_dpll_state <= i_rx_phy_dpll_next_state; end end

always @(i_rx_phy_dpll_state or i_rx_phy_rx_en or(i_rx_phy_rxd_r != i_rx_phy_rxd_s)) begin $display("achieve node: 54,0"); i_rx_phy_fs_ce_d = 1'b0; case (i_rx_phy_dpll_state) 
2'h0: begin  if (i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s)) begin $display("achieve node: 54,0,1");  $display("achieve node: 54,0,1,1"); i_rx_phy_dpll_next_state = 2'h0; end else begin $display("achieve node: 54,0,1,0");  i_rx_phy_dpll_next_state = 2'h1; end end 
2'h1: begin  i_rx_phy_fs_ce_d = 1'b1; $display("achieve node: 54,0,2");  if (i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s)) begin $display("achieve node: 54,0,2,1"); i_rx_phy_dpll_next_state = 2'h3; end else begin $display("achieve node: 54,0,2,0");  i_rx_phy_dpll_next_state = 2'h2; end end 
2'h2: begin  if (i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s)) begin $display("achieve node: 54,0,3");  $display("achieve node: 54,0,3,1"); i_rx_phy_dpll_next_state = 2'h0; end else begin $display("achieve node: 54,0,3,0");  i_rx_phy_dpll_next_state = 2'h3; end end 
2'h3: begin  if (i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s)) begin $display("achieve node: 54,0,4");  $display("achieve node: 54,0,4,1"); i_rx_phy_dpll_next_state = 2'h0; end else begin $display("achieve node: 54,0,4,0");  i_rx_phy_dpll_next_state = 2'h0; end end endcase end

always @(posedge clk) begin $display("achieve node: 55,1"); i_rx_phy_fs_ce_r1 <= i_rx_phy_fs_ce_d; end

always @(posedge clk) begin $display("achieve node: 56,1"); i_rx_phy_fs_ce_r2 <= i_rx_phy_fs_ce_r1; end

always @(posedge clk) begin $display("achieve node: 57,1"); i_rx_phy_fs_ce <= i_rx_phy_fs_ce_r2; end

always @(posedge clk or negedge rst) begin $display("achieve node: 58,1"); if (!(rst)) begin $display("achieve node: 58,1,1"); i_rx_phy_fs_state <= 3'h0; end else begin $display("achieve node: 58,1,0");  i_rx_phy_fs_state <= i_rx_phy_fs_next_state; end end

always @ ( i_rx_phy_fs_state or i_rx_phy_fs_ce or ( !( i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s ) or ( i_rx_phy_rxdp_s & !( i_rx_phy_rxdn_s) ) or i_rx_phy_rx_en or i_rx_phy_rx_active or ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) ) or i_rx_phy_se0_s) begin 
    i_rx_phy_synced_d = 1'b0; i_rx_phy_sync_err_d = 1'b0; i_rx_phy_fs_next_state = i_rx_phy_fs_state; 
    if ( ( ( i_rx_phy_fs_ce && !( i_rx_phy_rx_active) ) && !( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) )) ) && !( i_rx_phy_se0_s) ) begin  
        begin $display("achieve node: 59,0,1"); end 
        case (i_rx_phy_fs_state) 
        3'h0: begin  if ((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en) begin $display("achieve node: 59,0,1,1");  $display("achieve node: 59,0,1,1,1"); i_rx_phy_fs_next_state = 3'h1; end end 
        3'h1: begin  if ((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en) begin $display("achieve node: 59,0,1,2");  $display("achieve node: 59,0,1,2,1"); i_rx_phy_fs_next_state = 3'h2; end else begin $display("achieve node: 59,0,1,2,0");  i_rx_phy_sync_err_d = 1'b1; i_rx_phy_fs_next_state = 3'h0; end end 
        3'h2: begin  if ((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en) begin $display("achieve node: 59,0,1,3");  $display("achieve node: 59,0,1,3,1"); i_rx_phy_fs_next_state = 3'h3; end else begin $display("achieve node: 59,0,1,3,0");  i_rx_phy_sync_err_d = 1'b1; i_rx_phy_fs_next_state = 3'h0; end end 
        3'h3: begin  if ((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en) begin $display("achieve node: 59,0,1,4");  $display("achieve node: 59,0,1,4,1"); i_rx_phy_fs_next_state = 3'h4; end else begin $display("achieve node: 59,0,1,4,0");  i_rx_phy_sync_err_d = 1'b1; i_rx_phy_fs_next_state = 3'h0; end end 
        3'h4: begin  if ((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en) begin $display("achieve node: 59,0,1,5");  $display("achieve node: 59,0,1,5,1"); i_rx_phy_fs_next_state = 3'h5; end else begin $display("achieve node: 59,0,1,5,0");  i_rx_phy_sync_err_d = 1'b1; i_rx_phy_fs_next_state = 3'h0; end end 
        3'h5: begin  if ((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en) begin $display("achieve node: 59,0,1,6");  $display("achieve node: 59,0,1,6,1"); i_rx_phy_fs_next_state = 3'h6; end else begin $display("achieve node: 59,0,1,6,0");  if ((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en) begin $display("achieve node: 59,0,1,6,0,1"); i_rx_phy_fs_next_state = 3'h0; i_rx_phy_synced_d = 1'b1; end else begin $display("achieve node: 59,0,1,6,0,0");  i_rx_phy_sync_err_d = 1'b1; i_rx_phy_fs_next_state = 3'h0; end end end 
        3'h6: begin  if ((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en) begin $display("achieve node: 59,0,1,7");  $display("achieve node: 59,0,1,7,1"); i_rx_phy_fs_next_state = 3'h7; end else begin $display("achieve node: 59,0,1,7,0");  i_rx_phy_sync_err_d = 1'b1; i_rx_phy_fs_next_state = 3'h0; end end 
        3'h7: begin  if (!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) begin $display("achieve node: 59,0,1,8");  $display("achieve node: 59,0,1,8,1"); i_rx_phy_synced_d = 1'b1; end i_rx_phy_fs_next_state = 3'h0; end endcase end end

always @(posedge clk or negedge rst) begin $display("achieve node: 60,1"); if (!(rst)) begin $display("achieve node: 60,1,1"); i_rx_phy_rx_active <= 1'b0; end else begin $display("achieve node: 60,1,0");  if (i_rx_phy_synced_d && i_rx_phy_rx_en) begin $display("achieve node: 60,1,0,1"); i_rx_phy_rx_active <= 1'b1; end else begin $display("achieve node: 60,1,0,0");  if ((!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_valid_r) begin $display("achieve node: 60,1,0,0,1"); i_rx_phy_rx_active <= 1'b0; end end end end

always @(posedge clk) begin $display("achieve node: 61,1"); if (i_rx_phy_rx_valid) begin $display("achieve node: 61,1,1"); i_rx_phy_rx_valid_r <= 1'b1; end else begin $display("achieve node: 61,1,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 61,1,0,1"); i_rx_phy_rx_valid_r <= 1'b0; end end end

always @(posedge clk) begin $display("achieve node: 62,1"); if (i_rx_phy_fs_ce) begin $display("achieve node: 62,1,1"); i_rx_phy_sd_r <= i_rx_phy_rxd_s; end end

always @(posedge clk or negedge rst) begin $display("achieve node: 63,1"); if (!(rst)) begin $display("achieve node: 63,1,1"); i_rx_phy_sd_nrzi <= 1'b0; end else begin $display("achieve node: 63,1,0");  if (!(i_rx_phy_rx_active)) begin $display("achieve node: 63,1,0,1"); i_rx_phy_sd_nrzi <= 1'b1; end else begin $display("achieve node: 63,1,0,0");  if (i_rx_phy_rx_active && i_rx_phy_fs_ce) begin $display("achieve node: 63,1,0,0,1"); i_rx_phy_sd_nrzi <= !((i_rx_phy_rxd_s ^ i_rx_phy_sd_r)); end end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 64,1"); if (!(rst)) begin $display("achieve node: 64,1,1"); i_rx_phy_one_cnt <= 3'h0; end else begin $display("achieve node: 64,1,0");  if (!(i_rx_phy_shift_en)) begin $display("achieve node: 64,1,0,1"); i_rx_phy_one_cnt <= 3'h0; end else begin $display("achieve node: 64,1,0,0");  if (i_rx_phy_fs_ce) begin $display("achieve node: 64,1,0,0,1"); if (!(i_rx_phy_sd_nrzi) || (i_rx_phy_one_cnt == 3'h6)) begin $display("achieve node: 64,1,0,0,1,1"); i_rx_phy_one_cnt <= 3'h0; end else begin $display("achieve node: 64,1,0,0,1,0");  i_rx_phy_one_cnt <= (i_rx_phy_one_cnt + 3'h1); end end end end end

always @(posedge clk) begin $display("achieve node: 65,1"); i_rx_phy_bit_stuff_err <= ( ( ( ( ( i_rx_phy_one_cnt == 3'h6 ) & i_rx_phy_sd_nrzi ) & i_rx_phy_fs_ce ) & !( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) )) ) & i_rx_phy_rx_active ); end

always @(posedge clk) begin $display("achieve node: 66,1"); if (i_rx_phy_fs_ce) begin $display("achieve node: 66,1,1"); i_rx_phy_shift_en <= (i_rx_phy_synced_d | i_rx_phy_rx_active); end end

always @(posedge clk) begin $display("achieve node: 67,1"); if ((i_rx_phy_fs_ce && i_rx_phy_shift_en) && !((i_rx_phy_one_cnt == 3'h6))) begin $display("achieve node: 67,1,1"); i_rx_phy_hold_reg <= {i_rx_phy_sd_nrzi, i_rx_phy_hold_reg[7:1]}; end end

always @(posedge clk or negedge rst) begin $display("achieve node: 68,1"); if (!(rst)) begin $display("achieve node: 68,1,1"); i_rx_phy_bit_cnt <= 3'b0; end else begin $display("achieve node: 68,1,0");  if (!(i_rx_phy_shift_en)) begin $display("achieve node: 68,1,0,1"); i_rx_phy_bit_cnt <= 3'h0; end else begin $display("achieve node: 68,1,0,0");  if (i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6))) begin $display("achieve node: 68,1,0,0,1"); i_rx_phy_bit_cnt <= (i_rx_phy_bit_cnt + 3'h1); end end end end

always @(posedge clk or negedge rst) begin $display("achieve node: 69,1"); if (!(rst)) begin $display("achieve node: 69,1,1"); i_rx_phy_rx_valid1 <= 1'b0; end else begin $display("achieve node: 69,1,0");  if ((i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6))) && (i_rx_phy_bit_cnt == 3'h7)) begin $display("achieve node: 69,1,0,1"); i_rx_phy_rx_valid1 <= 1'b1; end else begin $display("achieve node: 69,1,0,0");  if ((i_rx_phy_rx_valid1 && i_rx_phy_fs_ce) && !((i_rx_phy_one_cnt == 3'h6))) begin $display("achieve node: 69,1,0,0,1"); i_rx_phy_rx_valid1 <= 1'b0; end end end end

always @(posedge clk) begin $display("achieve node: 70,1"); i_rx_phy_rx_valid <= ((!((i_rx_phy_one_cnt == 3'h6)) & i_rx_phy_rx_valid1) & i_rx_phy_fs_ce); end

always @(posedge clk) begin $display("achieve node: 71,1"); i_rx_phy_se0_r <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s)); end

always @(posedge clk) begin $display("achieve node: 72,1"); i_rx_phy_byte_err <= ( ( ( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) ) & !( i_rx_phy_se0_r) ) & |( i_rx_phy_bit_cnt[2:1]) ) & i_rx_phy_rx_active ); end

endmodule

