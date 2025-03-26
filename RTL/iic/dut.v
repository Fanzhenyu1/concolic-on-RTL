module i2c_master_top (    wb_clk_i,    rst_i,    wb_adr_i,    wb_dat_i,    wb_dat_o,    wb_we_i,    wb_stb_i,    wb_cyc_i,    wb_ack_o,    wb_inta_o,    scl_pad_i,    scl_pad_o,    scl_padoen_o,    sda_pad_i,    sda_pad_o,    sda_padoen_o);

 input wire wb_clk_i;

 input wire rst_i;

 input wire [2:0] wb_adr_i;

 input wire [7:0] wb_dat_i;

 output reg [7:0] wb_dat_o;

 input wire wb_we_i;

 input wire wb_stb_i;

 input wire wb_cyc_i;

 output reg wb_ack_o;

 output reg wb_inta_o;

 input wire scl_pad_i;

 output wire scl_pad_o;

 output wire scl_padoen_o;

 input wire sda_pad_i;

 output wire sda_pad_o;

 output wire sda_padoen_o;



 

 

 reg [15:0] prer;

 reg [7:0] ctr;

 reg [7:0] txr;

 reg [7:0] cr;

 reg rxack;

 reg tip;

 reg irq_flag;

 wire i2c_busy;

 reg al;

 wire wb_wacc = ((wb_cyc_i & wb_stb_i) & wb_we_i);

 wire sta = cr[7];

 wire sto = cr[6];

 wire rd = cr[5];

 wire wr = cr[4];

 wire ack = cr[3];

 wire iack = cr[0];

 wire [7:0] byte_controller_dout;

 wire byte_controller_i2c_busy;

 wire byte_controller_i2c_al;

 reg byte_controller_cmd_ack;

 reg byte_controller_ack_out;

 reg [3:0] byte_controller_core_cmd;

 reg byte_controller_core_txd;

 reg [7:0] byte_controller_sr;

 reg byte_controller_shift;

 reg byte_controller_ld;

 reg [2:0] byte_controller_dcnt;

 reg [4:0] byte_controller_c_state;

 reg byte_controller_target;

 wire byte_controller_bit_controller_scl_o;

 wire byte_controller_bit_controller_sda_o;

 reg byte_controller_bit_controller_cmd_ack;

 reg byte_controller_bit_controller_busy;

 reg byte_controller_bit_controller_al;

 reg byte_controller_bit_controller_dout;

 reg byte_controller_bit_controller_scl_oen;

 reg byte_controller_bit_controller_sda_oen;

 reg byte_controller_bit_controller_sSCL;

 reg byte_controller_bit_controller_sSDB;

 reg byte_controller_bit_controller_dscl_oen;

 reg byte_controller_bit_controller_sda_chk;

 reg byte_controller_bit_controller_clk_en;

 reg [15:0] byte_controller_bit_controller_cnt;

 reg [16:0] byte_controller_bit_controller_c_state;

 reg byte_controller_bit_controller_dSCL;

 reg byte_controller_bit_controller_dSDA;

 reg byte_controller_bit_controller_sta_condition;

 reg byte_controller_bit_controller_sto_condition;

 reg byte_controller_bit_controller_cmd_stop;

always @(posedge wb_clk_i) begin $display("achieve node: 0,1"); wb_ack_o <= ((wb_cyc_i & wb_stb_i) & ~(wb_ack_o)); end

always @(posedge wb_clk_i) begin $display("achieve node: 1,1"); case (wb_adr_i) 3'b000: begin  wb_dat_o <= prer[7:0]; $display("achieve node: 1,1,1");  end 3'b001: begin  wb_dat_o <= prer[15:8]; $display("achieve node: 1,1,2");  end 3'b010: begin  wb_dat_o <= ctr; $display("achieve node: 1,1,3");  end 3'b011: begin  wb_dat_o <= byte_controller_dout; $display("achieve node: 1,1,4");  end 3'b100: begin  wb_dat_o <= {rxack, i2c_busy, al, 3'h0, tip, irq_flag}; $display("achieve node: 1,1,5");  end 3'b101: begin  wb_dat_o <= txr; $display("achieve node: 1,1,6");  end 3'b110: begin  wb_dat_o <= cr; $display("achieve node: 1,1,7");  end 3'b111: begin  wb_dat_o <= 0; $display("achieve node: 1,1,8");  end endcase end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 2,1"); if (!(rst_i)) begin $display("achieve node: 2,1,1"); prer <= 16'hffff; ctr <= 8'h0; txr <= 8'h0; end else begin $display("achieve node: 2,1,0"); if (wb_wacc) begin $display("achieve node: 2,1,0,1"); case (wb_adr_i) 3'b000: begin  prer <= {prer[15:8], wb_dat_i}; $display("achieve node: 2,1,0,1,1");  end 3'b001: begin  prer <= {wb_dat_i, prer[7:0]}; $display("achieve node: 2,1,0,1,2");  end 3'b010: begin  ctr <= wb_dat_i; $display("achieve node: 2,1,0,1,3");  end 3'b011: begin  txr <= wb_dat_i; $display("achieve node: 2,1,0,1,4");  end endcase end end end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 3,1"); if (~(rst_i)) begin $display("achieve node: 3,1,1"); cr <= 8'h0; end else begin $display("achieve node: 3,1,0"); if (wb_wacc) begin $display("achieve node: 3,1,0,1"); if (ctr[7] & (wb_adr_i == 3'b100)) begin $display("achieve node: 3,1,0,1,1"); cr <= wb_dat_i; end end else begin $display("achieve node: 3,1,0,1,0"); if (byte_controller_cmd_ack | byte_controller_i2c_al) begin $display("achieve node: 3,1,0,1,0,1"); cr <= {4'h0, cr[3:0]}; end cr <= {cr[7:3], 3'b0}; end end end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 4,1"); if (!(rst_i)) begin $display("achieve node: 4,1,1"); al <= 1'b0; rxack <= 1'b0; tip <= 1'b0; irq_flag <= 1'b0; end else begin $display("achieve node: 4,1,0"); al <= (byte_controller_i2c_al | (al & ~(sta))); rxack <= byte_controller_ack_out; tip <= (rd | wr); irq_flag <= (((byte_controller_cmd_ack | byte_controller_i2c_al) | irq_flag) & ~(iack)); end end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 5,1"); if (!(rst_i)) begin $display("achieve node: 5,1,1"); wb_inta_o <= 1'b0; end else begin $display("achieve node: 5,1,0"); wb_inta_o <= (irq_flag && ctr[6]); end end

 assign i2c_busy = byte_controller_bit_controller_busy;

 assign scl_pad_o = 1'b0;

 assign scl_padoen_o = byte_controller_bit_controller_scl_oen;

 assign sda_pad_o = 1'b0;

 assign sda_padoen_o = byte_controller_bit_controller_sda_oen;

 assign byte_controller_i2c_busy = byte_controller_bit_controller_busy;

 assign byte_controller_i2c_al = byte_controller_bit_controller_al;

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 13,1"); if (~(rst_i)) begin $display("achieve node: 13,1,1"); byte_controller_bit_controller_dscl_oen <= 1'b0; end else begin $display("achieve node: 13,1,0"); byte_controller_bit_controller_dscl_oen <= byte_controller_bit_controller_scl_oen; end end

always @(posedge wb_clk_i or negedge rst_i) begin 
    $display("achieve node: 14,1"); 
    if (~(rst_i)) begin $display("achieve node: 14,1,1"); byte_controller_bit_controller_cnt <= 16'h0; byte_controller_bit_controller_clk_en <= 1'b1; 
    end else begin $display("achieve node: 14,1,0"); 
        if (~|(byte_controller_bit_controller_cnt) || ~(ctr[7])) begin 
            $display("achieve node: 14,1,0,1"); 
            if ( ~( ( byte_controller_bit_controller_dscl_oen && !( byte_controller_bit_controller_sSCL) )) ) begin  
                begin $display("achieve node: 14,1,0,1,1"); end byte_controller_bit_controller_cnt <= prer; byte_controller_bit_controller_clk_en <= 1'b1; end 
            else begin $display("achieve node: 14,1,0,1,0"); byte_controller_bit_controller_cnt <= byte_controller_bit_controller_cnt; byte_controller_bit_controller_clk_en <= 1'b0; end 
        end else begin 
            $display("achieve node: 14,1,0,0"); byte_controller_bit_controller_cnt <= (byte_controller_bit_controller_cnt - 16'h1); byte_controller_bit_controller_clk_en <= 1'b0; 
            end 
            end 
            end

always @(posedge wb_clk_i or negedge rst_i) begin 
    $display("achieve node: 15,1"); 
    if (~(rst_i)) begin 
        $display("achieve node: 15,1,1"); byte_controller_bit_controller_sSCL <= 1'b1; byte_controller_bit_controller_sSDB <= 1'b1; byte_controller_bit_controller_dSCL <= 1'b1; byte_controller_bit_controller_dSDA <= 1'b1; 
    end else begin 
        $display("achieve node: 15,1,0"); byte_controller_bit_controller_sSCL <= scl_pad_i; byte_controller_bit_controller_sSDB <= sda_pad_i; byte_controller_bit_controller_dSCL <= byte_controller_bit_controller_sSCL; byte_controller_bit_controller_dSDA <= byte_controller_bit_controller_sSDB; end end

always @(posedge wb_clk_i or negedge rst_i) begin 
    $display("achieve node: 16,1"); 
    if (~(rst_i)) begin 
        $display("achieve node: 16,1,1"); byte_controller_bit_controller_sta_condition <= 1'b0; byte_controller_bit_controller_sto_condition <= 1'b0; 
    end else begin 
        $display("achieve node: 16,1,0"); byte_controller_bit_controller_sta_condition <= ( ( ~( byte_controller_bit_controller_sSDB) & byte_controller_bit_controller_dSDA ) & byte_controller_bit_controller_sSCL ); byte_controller_bit_controller_sto_condition <= ( ( byte_controller_bit_controller_sSDB & ~( byte_controller_bit_controller_dSDA) ) & byte_controller_bit_controller_sSCL ); end end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 17,1"); if (!(rst_i)) begin $display("achieve node: 17,1,1"); byte_controller_bit_controller_busy <= 1'b0; end else begin $display("achieve node: 17,1,0"); byte_controller_bit_controller_busy <= ( ( byte_controller_bit_controller_sta_condition | byte_controller_bit_controller_busy ) & ~( byte_controller_bit_controller_sto_condition) ); end end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 18,1"); if (~(rst_i)) begin $display("achieve node: 18,1,1"); byte_controller_bit_controller_cmd_stop <= 1'b0; end else begin $display("achieve node: 18,1,0"); if (byte_controller_bit_controller_clk_en) begin $display("achieve node: 18,1,0,1"); byte_controller_bit_controller_cmd_stop <= (byte_controller_core_cmd == 4'b0010); end end end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 19,1"); if (~(rst_i)) begin $display("achieve node: 19,1,1"); byte_controller_bit_controller_al <= 1'b0; end else begin $display("achieve node: 19,1,0"); byte_controller_bit_controller_al <= ( ( ( byte_controller_bit_controller_sda_chk & ~( byte_controller_bit_controller_sSDB) ) & byte_controller_bit_controller_sda_oen ) | ( ( |( byte_controller_bit_controller_c_state) & byte_controller_bit_controller_sto_condition ) & ~( byte_controller_bit_controller_cmd_stop) ) ); end end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 20,1"); if (~(rst_i)) begin $display("achieve node: 20,1,1"); byte_controller_bit_controller_dout <= 1'b0; end else begin $display("achieve node: 20,1,0"); if (byte_controller_bit_controller_sSCL & ~(byte_controller_bit_controller_dSCL)) begin $display("achieve node: 20,1,0,1"); byte_controller_bit_controller_dout <= byte_controller_bit_controller_sSDB; end end end

always @(posedge wb_clk_i or negedge rst_i) begin 
    $display("achieve node: 21,1"); 
    if (!(rst_i)) begin 
        $display("achieve node: 21,1,1"); byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000; byte_controller_bit_controller_cmd_ack <= 1'b0; byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; 
    end else begin 
        $display("achieve node: 21,1,0"); 
        if (byte_controller_bit_controller_al) begin 
            $display("achieve node: 21,1,0,1"); byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000; byte_controller_bit_controller_cmd_ack <= 1'b0; byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; 
        end else begin 
            $display("achieve node: 21,1,0,0"); byte_controller_bit_controller_cmd_ack <= 1'b0; 
            if (byte_controller_bit_controller_clk_en) begin 
                $display("achieve node: 21,1,0,0,1"); 
                case (byte_controller_bit_controller_c_state) 
                17'b0_0000_0000_0000_0000: begin  
                    case (byte_controller_core_cmd) 
                    4'b0001: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0001; $display("achieve node: 21,1,0,0,1,1,1");  end 
                    4'b0010: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0010_0000; $display("achieve node: 21,1,0,0,1,1,2");  end 
                    4'b0100: begin  byte_controller_bit_controller_c_state <= 17'b0_0010_0000_0000_0000; $display("achieve node: 21,1,0,0,1,1,3");  end 
                    4'b1000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0010_0000_0000; $display("achieve node: 21,1,0,0,1,1,4");  end 
                    default: begin byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000; $display("achieve node: 21,1,0,0,1,1,5"); end 
                    endcase 
                    byte_controller_bit_controller_scl_oen <= byte_controller_bit_controller_scl_oen; byte_controller_bit_controller_sda_oen <= byte_controller_bit_controller_sda_oen; byte_controller_bit_controller_sda_chk <= 1'b0; end 
                17'b0_0000_0000_0000_0001: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0010; $display("achieve node: 21,1,0,0,1,2");  byte_controller_bit_controller_scl_oen <= byte_controller_bit_controller_scl_oen; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; end
                17'b0_0000_0000_0000_0010: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0100; $display("achieve node: 21,1,0,0,1,3");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; end 
                17'b0_0000_0000_0000_0100: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_1000; $display("achieve node: 21,1,0,0,1,4");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b0; byte_controller_bit_controller_sda_chk <= 1'b0; end 
                17'b0_0000_0000_0000_1000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0001_0000; $display("achieve node: 21,1,0,0,1,5");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b0; byte_controller_bit_controller_sda_chk <= 1'b0; end 
                17'b0_0000_0000_0001_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000; $display("achieve node: 21,1,0,0,1,6");  byte_controller_bit_controller_cmd_ack <= 1'b1; byte_controller_bit_controller_scl_oen <= 1'b0; byte_controller_bit_controller_sda_oen <= 1'b0; byte_controller_bit_controller_sda_chk <= 1'b0; end 
                17'b0_0000_0000_0010_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0100_0000; $display("achieve node: 21,1,0,0,1,7");  byte_controller_bit_controller_scl_oen <= 1'b0; byte_controller_bit_controller_sda_oen <= 1'b0; byte_controller_bit_controller_sda_chk <= 1'b0; end 
                17'b0_0000_0000_0100_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_1000_0000; $display("achieve node: 21,1,0,0,1,8");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b0; byte_controller_bit_controller_sda_chk <= 1'b0; end 17'b0_0000_0000_1000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0001_0000_0000; $display("achieve node: 21,1,0,0,1,9");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b0; byte_controller_bit_controller_sda_chk <= 1'b0; end 17'b0_0000_0001_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000; $display("achieve node: 21,1,0,0,1,10");  byte_controller_bit_controller_cmd_ack <= 1'b1; byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; end 17'b0_0000_0010_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0100_0000_0000; $display("achieve node: 21,1,0,0,1,11");  byte_controller_bit_controller_scl_oen <= 1'b0; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; end 17'b0_0000_0100_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_1000_0000_0000; $display("achieve node: 21,1,0,0,1,12");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; end 17'b0_0000_1000_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0001_0000_0000_0000; $display("achieve node: 21,1,0,0,1,13");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; end 17'b0_0001_0000_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000; $display("achieve node: 21,1,0,0,1,14");  byte_controller_bit_controller_cmd_ack <= 1'b1; byte_controller_bit_controller_scl_oen <= 1'b0; byte_controller_bit_controller_sda_oen <= 1'b1; byte_controller_bit_controller_sda_chk <= 1'b0; end 17'b0_0010_0000_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0100_0000_0000_0000; $display("achieve node: 21,1,0,0,1,15");  byte_controller_bit_controller_scl_oen <= 1'b0; byte_controller_bit_controller_sda_oen <= byte_controller_core_txd; byte_controller_bit_controller_sda_chk <= 1'b0; end 17'b0_0100_0000_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_1000_0000_0000_0000; $display("achieve node: 21,1,0,0,1,16");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= byte_controller_core_txd; byte_controller_bit_controller_sda_chk <= 1'b1; end 17'b0_1000_0000_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b1_0000_0000_0000_0000; $display("achieve node: 21,1,0,0,1,17");  byte_controller_bit_controller_scl_oen <= 1'b1; byte_controller_bit_controller_sda_oen <= byte_controller_core_txd; byte_controller_bit_controller_sda_chk <= 1'b1; end 17'b1_0000_0000_0000_0000: begin  byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000; $display("achieve node: 21,1,0,0,1,18");  byte_controller_bit_controller_cmd_ack <= 1'b1; byte_controller_bit_controller_scl_oen <= 1'b0; byte_controller_bit_controller_sda_oen <= byte_controller_core_txd; byte_controller_bit_controller_sda_chk <= 1'b0; end endcase end end end end

 assign byte_controller_dout = byte_controller_sr;

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 23,1"); if (!(rst_i)) begin $display("achieve node: 23,1,1"); byte_controller_sr <= 8'h0; end else begin $display("achieve node: 23,1,0"); if (byte_controller_ld) begin $display("achieve node: 23,1,0,1"); byte_controller_sr <= txr; end else begin $display("achieve node: 23,1,0,0"); if (byte_controller_shift) begin $display("achieve node: 23,1,0,0,1"); byte_controller_sr <= {byte_controller_sr[6:0], byte_controller_bit_controller_dout}; end end end end

always @(posedge wb_clk_i or negedge rst_i) begin $display("achieve node: 24,1"); if (!(rst_i)) begin $display("achieve node: 24,1,1"); byte_controller_dcnt <= 3'h0; end else begin $display("achieve node: 24,1,0"); if (byte_controller_ld) begin $display("achieve node: 24,1,0,1"); byte_controller_dcnt <= 3'h7; end else begin $display("achieve node: 24,1,0,0"); if (byte_controller_shift) begin $display("achieve node: 24,1,0,0,1"); byte_controller_dcnt <= (byte_controller_dcnt - 3'h1); end end end end

always @(posedge wb_clk_i or negedge rst_i) begin 
    $display("achieve node: 25,1"); 
    if (!(rst_i)) begin $display("achieve node: 25,1,1"); byte_controller_core_cmd <= 4'b0000; byte_controller_core_txd <= 1'b0; byte_controller_shift <= 1'b0; byte_controller_ld <= 1'b0; byte_controller_cmd_ack <= 1'b0; byte_controller_c_state <= 5'b0_0000; byte_controller_ack_out <= 1'b0; 
    end else begin 
        $display("achieve node: 25,1,0"); 
        if (byte_controller_bit_controller_al) begin 
            $display("achieve node: 25,1,0,1"); byte_controller_core_cmd <= 4'b0000; byte_controller_core_txd <= 1'b0; byte_controller_shift <= 1'b0; byte_controller_ld <= 1'b0; byte_controller_cmd_ack <= 1'b0; byte_controller_c_state <= 5'b0_0000; byte_controller_ack_out <= 1'b0; 
        end else begin 
            $display("achieve node: 25,1,0,0"); byte_controller_core_txd <= byte_controller_sr[7]; byte_controller_shift <= 1'b0; byte_controller_ld <= 1'b0; byte_controller_cmd_ack <= 1'b0; 
            case (byte_controller_c_state) 
            5'b0_0000: begin  
                if (((rd | wr) | sto) & ~(byte_controller_cmd_ack)) begin 
                    $display("achieve node: 25,1,0,0,1");  $display("achieve node: 25,1,0,0,1,1"); 
                    if (sta) begin $display("achieve node: 25,1,0,0,1,1,1"); byte_controller_target <= 1; byte_controller_c_state <= 5'b0_0001; byte_controller_core_cmd <= 4'b0001; 
                    end else begin 
                        $display("achieve node: 25,1,0,0,1,1,0"); 
                        if (rd) begin $display("achieve node: 25,1,0,0,1,1,0,1"); byte_controller_c_state <= 5'b0_0010; byte_controller_core_cmd <= 4'b1000; 
                        end else begin $display("achieve node: 25,1,0,0,1,1,0,0"); 
                            if (wr) begin 
                                $display("achieve node: 25,1,0,0,1,1,0,0,1"); byte_controller_c_state <= 5'b0_0100; byte_controller_core_cmd <= 4'b0100; 
                            end else begin 
                                $display("achieve node: 25,1,0,0,1,1,0,0,0"); byte_controller_c_state <= 5'b1_0000; byte_controller_core_cmd <= 4'b0010; 
                            end end end 
                    byte_controller_ld <= 1'b1; end end 
            5'b0_0001: begin  
                if (byte_controller_bit_controller_cmd_ack) begin $display("achieve node: 25,1,0,0,2");  $display("achieve node: 25,1,0,0,2,1"); if (rd) begin $display("achieve node: 25,1,0,0,2,1,1"); byte_controller_c_state <= 5'b0_0010; byte_controller_core_cmd <= 4'b1000; end else begin $display("achieve node: 25,1,0,0,2,1,0"); byte_controller_c_state <= 5'b0_0100; byte_controller_core_cmd <= 4'b0100; end byte_controller_ld <= 1'b1; end end 
            5'b0_0100: begin  
                if (byte_controller_bit_controller_cmd_ack) begin 
                    $display("achieve node: 25,1,0,0,3");  $display("achieve node: 25,1,0,0,3,1"); 
                    if (~(|(byte_controller_dcnt))) begin 
                        $display("achieve node: 25,1,0,0,3,1,1"); byte_controller_c_state <= 5'b0_1000; byte_controller_core_cmd <= 4'b1000; 
                    end else begin 
                        $display("achieve node: 25,1,0,0,3,1,0"); byte_controller_c_state <= 5'b0_0100; byte_controller_core_cmd <= 4'b0100; byte_controller_shift <= 1'b1; 
                    end end end 
            5'b0_0010: begin  
                if (byte_controller_bit_controller_cmd_ack) begin $display("achieve node: 25,1,0,0,4");  $display("achieve node: 25,1,0,0,4,1"); if (~(|(byte_controller_dcnt))) begin $display("achieve node: 25,1,0,0,4,1,1"); byte_controller_c_state <= 5'b0_1000; byte_controller_core_cmd <= 4'b0100; end else begin $display("achieve node: 25,1,0,0,4,1,0"); byte_controller_c_state <= 5'b0_0010; byte_controller_core_cmd <= 4'b1000; end byte_controller_shift <= 1'b1; byte_controller_core_txd <= ack; end end 
            5'b0_1000: begin  
                if (byte_controller_bit_controller_cmd_ack) begin $display("achieve node: 25,1,0,0,5");  $display("achieve node: 25,1,0,0,5,1"); if (sto) begin $display("achieve node: 25,1,0,0,5,1,1"); byte_controller_c_state <= 5'b1_0000; byte_controller_core_cmd <= 4'b0010; end else begin $display("achieve node: 25,1,0,0,5,1,0"); byte_controller_c_state <= 5'b0_0000; byte_controller_core_cmd <= 4'b0000; byte_controller_cmd_ack <= 1'b1; end byte_controller_ack_out <= byte_controller_bit_controller_dout; byte_controller_core_txd <= 1'b1; end else begin $display("achieve node: 25,1,0,0,5,0"); byte_controller_core_txd <= ack; end end 
            5'b1_0000: begin  
                if (byte_controller_bit_controller_cmd_ack) begin $display("achieve node: 25,1,0,0,6");  $display("achieve node: 25,1,0,0,6,1"); byte_controller_c_state <= 5'b0_0000; byte_controller_core_cmd <= 4'b0000; byte_controller_cmd_ack <= 1'b1; end end 
            endcase 
        end end end

endmodule

