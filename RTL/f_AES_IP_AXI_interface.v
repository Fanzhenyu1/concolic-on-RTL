module AES_IP_AXI_interface #(
    parameter integer C_S_AXI_ID_WIDTH = 4,
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 32,
    parameter integer C_S_AXI_AWUSER_WIDTH = 0,
    parameter integer C_S_AXI_ARUSER_WIDTH = 0,
    parameter integer C_S_AXI_WUSER_WIDTH = 0,
    parameter integer C_S_AXI_RUSER_WIDTH = 0,
    parameter integer C_S_AXI_BUSER_WIDTH = 0
) (
    /* -------------------------------------------------------------------------- */
    /*                                User defined                                */
    /* -------------------------------------------------------------------------- */
    //----------------------------------------------------------------
    //output to AES core
    //----------------------------------------------------------------
    output wire                          rst_n_to_AES_core,
    output reg                           start,
    output wire [C_S_AXI_DATA_WIDTH-1:0] input_text,
    output wire [C_S_AXI_DATA_WIDTH-1:0] key,
    output wire [C_S_AXI_DATA_WIDTH-1:0] IV,
    output wire                          mode_of_enc_or_dec,
    output wire                          mode_of_ecb_or_cbc,
    //----------------------------------------------------------------
    //input from AES core
    //----------------------------------------------------------------
    input  wire                          done,
    input  wire [C_S_AXI_DATA_WIDTH-1:0] output_text,

    input wire [31:0] intermediate_data,

    output     bug_9_round_en,
    //----------------------------------------------------------------
    //output to interrupt controller
    //----------------------------------------------------------------
    output reg busy,
    output reg INT2,

    /* -------------------------------------------------------------------------- */
    /*                                  AXI4 Port                                 */
    /* -------------------------------------------------------------------------- */
    // Global Clock Signal
    input  wire                              S_AXI_ACLK,
    input  wire                              S_AXI_ARESETN,
    input  wire [    C_S_AXI_ID_WIDTH-1 : 0] S_AXI_AWID,
    input  wire [C_S_AXI_ADDR_WIDTH*4-1 : 0] S_AXI_AWADDR,    //change from 10bit to 40bit
    input  wire [                     7 : 0] S_AXI_AWLEN,
    input  wire [                     2 : 0] S_AXI_AWSIZE,
    input  wire [                     1 : 0] S_AXI_AWBURST,
    input  wire                              S_AXI_AWLOCK,
    input  wire [                     3 : 0] S_AXI_AWCACHE,
    input  wire [                     2 : 0] S_AXI_AWPROT,
    input  wire [                     3 : 0] S_AXI_AWQOS,
    input  wire [                     3 : 0] S_AXI_AWREGION,
    input  wire [C_S_AXI_AWUSER_WIDTH-1 : 0] S_AXI_AWUSER,
    input  wire                              S_AXI_AWVALID,
    output wire                              S_AXI_AWREADY,
    input  wire [  C_S_AXI_DATA_WIDTH-1 : 0] S_AXI_WDATA,
    input  wire [(C_S_AXI_DATA_WIDTH/2)-1:0] S_AXI_WSTRB,
    input  wire                              S_AXI_WLAST,
    input  wire [ C_S_AXI_WUSER_WIDTH-1 : 0] S_AXI_WUSER,
    input  wire                              S_AXI_WVALID,
    output wire                              S_AXI_WREADY,
    output wire [    C_S_AXI_ID_WIDTH-1 : 0] S_AXI_BID,
    output wire [                     1 : 0] S_AXI_BRESP,
    output wire [ C_S_AXI_BUSER_WIDTH-1 : 0] S_AXI_BUSER,
    output wire                              S_AXI_BVALID,
    input  wire                              S_AXI_BREADY,
    input  wire [    C_S_AXI_ID_WIDTH-1 : 0] S_AXI_ARID,
    input  wire [  C_S_AXI_ADDR_WIDTH-1 : 0] S_AXI_ARADDR,
    input  wire [                     7 : 0] S_AXI_ARLEN,
    input  wire [                     2 : 0] S_AXI_ARSIZE,
    input  wire [                     1 : 0] S_AXI_ARBURST,
    input  wire                              S_AXI_ARLOCK,
    input  wire [                     3 : 0] S_AXI_ARCACHE,
    input  wire [                     2 : 0] S_AXI_ARPROT,
    input  wire [                     3 : 0] S_AXI_ARQOS,
    input  wire [                     3 : 0] S_AXI_ARREGION,
    input  wire [C_S_AXI_ARUSER_WIDTH-1 : 0] S_AXI_ARUSER,
    input  wire                              S_AXI_ARVALID,
    output wire                              S_AXI_ARREADY,
    output wire [    C_S_AXI_ID_WIDTH-1 : 0] S_AXI_RID,
    output wire [  C_S_AXI_DATA_WIDTH-1 : 0] S_AXI_RDATA,
    output wire [                     1 : 0] S_AXI_RRESP,
    output wire                              S_AXI_RLAST,
    output wire [ C_S_AXI_RUSER_WIDTH-1 : 0] S_AXI_RUSER,
    output wire                              S_AXI_RVALID,
    input  wire                              S_AXI_RREADY
);

  reg                              output_text_valid;


  // AXI4FULL signals
  reg  [ C_S_AXI_ADDR_WIDTH-1 : 0] axi_awaddr;
  reg                              axi_awready;
  reg                              axi_wready;
  reg  [                    1 : 0] axi_bresp;
  reg  [C_S_AXI_BUSER_WIDTH-1 : 0] axi_buser;
  reg                              axi_bvalid;
  reg  [ C_S_AXI_ADDR_WIDTH-1 : 0] axi_araddr;
  reg                              axi_arready;
  reg  [ C_S_AXI_DATA_WIDTH-1 : 0] axi_rdata;
  reg  [                    1 : 0] axi_rresp;
  reg                              axi_rlast;
  reg  [C_S_AXI_RUSER_WIDTH-1 : 0] axi_ruser;
  reg                              axi_rvalid;
  // aw_wrap_en determines wrap boundary and enables wrapping
  wire                             aw_wrap_en;
  // ar_wrap_en determines wrap boundary and enables wrapping
  wire                             ar_wrap_en;
  // aw_wrap_size is the size of the write transfer, the
  // write address wraps to a lower address if upper address
  // limit is reached
  wire [                     31:0] aw_wrap_size;
  // ar_wrap_size is the size of the read transfer, the
  // read address wraps to a lower address if upper address
  // limit is reached
  wire [                     31:0] ar_wrap_size;
  // The axi_awv_awr_flag flag marks the presence of write address valid
  reg                              axi_awv_awr_flag;
  //The axi_arv_arr_flag flag marks the presence of read address valid
  reg                              axi_arv_arr_flag;
  // The axi_awlen_cntr internal write address counter to keep track of beats in a burst transaction
  reg  [                      7:0] axi_awlen_cntr;
  //The axi_arlen_cntr internal read address counter to keep track of beats in a burst transaction
  reg  [                      7:0] axi_arlen_cntr;
  reg  [                      1:0] axi_arburst;
  reg  [                      1:0] axi_awburst;
  reg  [                      7:0] axi_arlen;
  reg  [                      7:0] axi_awlen;
  //local parameter for addressing 32 bit / 64 bit C_S_AXI_DATA_WIDTH
  //ADDR_LSB is used for addressing 32/64 bit registers/memories
  //ADDR_LSB = 2 for 32 bits (n downto 2) 
  //ADDR_LSB = 3 for 42 bits (n downto 3)

  localparam integer ADDR_LSB = (C_S_AXI_DATA_WIDTH / 32) + 1;
  localparam integer OPT_MEM_ADDR_BITS = 3;





  // I/O Connections assignments
  assign S_AXI_AWREADY = axi_awready;
  assign S_AXI_WREADY = axi_wready;
  assign S_AXI_BRESP = axi_bresp;
  assign S_AXI_BUSER = 1'b0;

  assign S_AXI_BVALID = axi_bvalid;
  assign S_AXI_ARREADY = axi_arready;
  assign S_AXI_RDATA = axi_rdata;
  assign S_AXI_RRESP = axi_rresp;
  assign S_AXI_RLAST = axi_rlast;
  assign S_AXI_RUSER = axi_ruser;
  assign S_AXI_RVALID = axi_rvalid;
  assign S_AXI_BID = S_AXI_AWID;
  assign S_AXI_RID = S_AXI_ARVALID ? S_AXI_ARID : S_AXI_RID;
  assign aw_wrap_size = (C_S_AXI_DATA_WIDTH / 8 * (axi_awlen));
  assign ar_wrap_size = (C_S_AXI_DATA_WIDTH / 8 * (axi_arlen));
  assign aw_wrap_en = ((axi_awaddr & aw_wrap_size) == aw_wrap_size) ? 1'b1 : 1'b0;
  assign ar_wrap_en = ((axi_araddr & ar_wrap_size) == ar_wrap_size) ? 1'b1 : 1'b0;


  /* --------------------------------- awready -------------------------------- */
  // Implement axi_awready generation
  // axi_awready is asserted for one S_AXI_ACLK clock cycle when both
  // S_AXI_AWVALID and S_AXI_WVALID are asserted. axi_awready is
  // de-asserted when reset is low.
  always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
      axi_awready      <=     1'b0;
      axi_awv_awr_flag <= 1'b0;
    end 
    else if (~axi_awready && S_AXI_AWVALID && ~axi_awv_awr_flag && ~axi_arv_arr_flag) begin
      axi_awready <= 1'b1;
      axi_awv_awr_flag <= 1'b1;
        // used for generation of bresp() and bvalid
    end
	  else if (S_AXI_WLAST && axi_wready) begin
      axi_awv_awr_flag <= 1'b0;
    end 
    else begin
      axi_awready <= 1'b0;
    end
  end


  /* ------------------------------- axi_awaddr latching ------------------------------- */
  // Implement axi_awaddr latching
  // This process is used to latch the address when both 
  // S_AXI_AWVALID and S_AXI_WVALID are valid. 
  always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
      axi_awaddr <= 0;
      axi_awlen_cntr <= 0;
      axi_awburst <= 0;
      axi_awlen <= 0;
    end else if (~axi_awready && S_AXI_AWVALID && ~axi_awv_awr_flag) begin
        // address latching 
        axi_awaddr[11:0] <= S_AXI_AWADDR[11:0];
        axi_awburst <= S_AXI_AWBURST;
        axi_awlen <= S_AXI_AWLEN;
        // start address of transfer
        axi_awlen_cntr <= 0;
      end else if ((axi_awlen_cntr <= axi_awlen) && axi_wready && S_AXI_WVALID) begin

        axi_awlen_cntr <= axi_awlen_cntr + 1;
        case (axi_awburst)
          2'b00: // fixed burst
	            // The write address for all the beats in the transaction are fixed
          begin
            axi_awaddr <= axi_awaddr;
            //for awsize = 4 bytes (010)
          end
          2'b01: //incremental burst
	            // The write address for all the beats in the transaction are increments by awsize
          begin
            axi_awaddr[C_S_AXI_ADDR_WIDTH - 1:ADDR_LSB] <= axi_awaddr[C_S_AXI_ADDR_WIDTH - 1:ADDR_LSB] + 1;
            //awaddr aligned to 4 byte boundary
            axi_awaddr[ADDR_LSB-1:0] <= {ADDR_LSB{1'b0}};
            //for awsize = 4 bytes (010)
          end
          2'b10:  //Wrapping burst
          // The write address wraps when the address reaches wrap boundary 
          if (aw_wrap_en) begin
            axi_awaddr <= (axi_awaddr - aw_wrap_size);
          end else begin
            axi_awaddr[C_S_AXI_ADDR_WIDTH - 1:ADDR_LSB] <= axi_awaddr[C_S_AXI_ADDR_WIDTH - 1:ADDR_LSB] + 1;
            axi_awaddr[ADDR_LSB-1:0] <= {ADDR_LSB{1'b0}};
          end
          default: axi_awaddr <= axi_awaddr[C_S_AXI_ADDR_WIDTH-1:ADDR_LSB] + 1;

        endcase
      end
  end


  /* ------------------------------- axi_wready ------------------------------- */
  // Implement axi_wready generation
  // axi_wready is asserted for one S_AXI_ACLK clock cycle when both
  // S_AXI_AWVALID and S_AXI_WVALID are asserted. axi_wready is 
  // de-asserted when reset is low. 
  always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
      axi_wready <= 1'b0;
    end else begin
      if (~axi_wready && S_AXI_WVALID && axi_awv_awr_flag) begin
        // slave can accept the write data
        axi_wready <= 1'b1;
      end  //else if (~axi_awv_awr_flag)
      else if (S_AXI_WLAST && axi_wready) begin
        axi_wready <= 1'b0;
      end
    end
  end

  /* -------------------------------- b channel ------------------------------- */
  // Implement write response logic generation
  // The write response and response valid signals are asserted by the slave 
  // when axi_wready, S_AXI_WVALID, axi_wready and S_AXI_WVALID are asserted.  
  // This marks the acceptance of address and indicates the status of 
  // write transaction.
  always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
      axi_bvalid <= 0;
      axi_bresp  <= 2'b0;
      //axi_buser <= 0;						//original
    end else begin
      if (axi_awv_awr_flag && axi_wready && S_AXI_WVALID && ~axi_bvalid && S_AXI_WLAST) begin
        axi_bvalid <= 1'b1;
        axi_bresp  <= 2'b0;
        // 'OKAY' response 
      end else begin
        if (S_AXI_BREADY && axi_bvalid) 
	          //check if bready is asserted while bvalid is high) 
	          //(there is a possibility that bready is always asserted high)   
	            begin
          axi_bvalid <= 1'b0;
        end
      end
    end
  end


  /* --------------------------------- arready -------------------------------- */
  // Implement axi_arready generation
  // axi_arready is asserted for one S_AXI_ACLK clock cycle when
  // S_AXI_ARVALID is asserted. axi_awready is 
  // de-asserted when reset (active low) is asserted. 
  // The read address is also latched when S_AXI_ARVALID is 
  // asserted. axi_araddr is reset to zero on reset assertion.
  always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
      axi_arready <= 1'b0;
      axi_arv_arr_flag <= 1'b0;
    end else begin
      if (~axi_arready && S_AXI_ARVALID && ~axi_awv_awr_flag && ~axi_arv_arr_flag) begin
        axi_arready <= 1'b1;
        axi_arv_arr_flag <= 1'b1;
      end
	      else if (axi_rvalid && S_AXI_RREADY && axi_arlen_cntr == axi_arlen)
	      // preparing to accept next address after current read completion
	        begin
        axi_arv_arr_flag <= 1'b0;
      end else begin
        axi_arready <= 1'b0;
      end
    end
  end


  /* --------------------------- axi_araddr latching -------------------------- */
  // Implement axi_araddr latching
  //This process is used to latch the address when both 
  //S_AXI_ARVALID and S_AXI_RVALID are valid. 
  always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
      axi_araddr     <= 0;
      axi_arlen_cntr <= 0;
      axi_arburst    <= 0;
      axi_arlen      <= 0;
      axi_rlast      <= 1'b0;
      axi_ruser      <= 0;  //need not axi_ruser
    end else begin
      if (~axi_arready && S_AXI_ARVALID && ~axi_arv_arr_flag) begin
        // address latching 
        axi_araddr[11:0] <= S_AXI_ARADDR[11:0];
        //axi_araddr <= S_AXI_ARADDR[C_S_AXI_ADDR_WIDTH - 1:0]; 
        axi_arburst <= S_AXI_ARBURST;
        axi_arlen <= S_AXI_ARLEN;
        // start address of transfer
        axi_arlen_cntr <= 0;
        axi_rlast <= 1'b0;
      end else if ((axi_arlen_cntr <= axi_arlen) && axi_rvalid && S_AXI_RREADY) begin

        axi_arlen_cntr <= axi_arlen_cntr + 1;
        axi_rlast <= 1'b0;

        case (axi_arburst)
          2'b00: // fixed burst
	             // The read address for all the beats in the transaction are fixed
          begin
            axi_araddr <= axi_araddr;
            //for arsize = 4 bytes (010)
          end
          2'b01: //incremental burst
	            // The read address for all the beats in the transaction are increments by awsize
          begin
            axi_araddr[C_S_AXI_ADDR_WIDTH - 1:ADDR_LSB] <= axi_araddr[C_S_AXI_ADDR_WIDTH - 1:ADDR_LSB] + 1;
            //araddr aligned to 4 byte boundary
            axi_araddr[ADDR_LSB-1:0] <= {ADDR_LSB{1'b0}};
            //for awsize = 4 bytes (010)
          end
          2'b10:  //Wrapping burst
          // The read address wraps when the address reaches wrap boundary 
          if (ar_wrap_en) begin
            axi_araddr <= (axi_araddr - ar_wrap_size);
          end else begin
            axi_araddr[C_S_AXI_ADDR_WIDTH - 1:ADDR_LSB] <= axi_araddr[C_S_AXI_ADDR_WIDTH - 1:ADDR_LSB] + 1;
            //araddr aligned to 4 byte boundary
            axi_araddr[ADDR_LSB-1:0] <= {ADDR_LSB{1'b0}};
          end
          default: //reserved (incremental burst for example)
	              begin
            axi_araddr <= axi_araddr[C_S_AXI_ADDR_WIDTH-1:ADDR_LSB] + 1;
            //for arsize = 4 bytes (010)
          end
        endcase
      end else if ((axi_arlen_cntr == axi_arlen) && ~axi_rlast && axi_arv_arr_flag) begin
        axi_rlast <= 1'b1;
      end else if (S_AXI_RREADY) begin
        axi_rlast <= 1'b0;
      end
    end
  end


  /* --------------------------------- rvalid --------------------------------- */
  // Implement axi_rvalid generation
  // axi_rvalid is asserted for one S_AXI_ACLK clock cycle when both 
  // S_AXI_ARVALID and axi_arready are asserted. The slave registers 
  // data are available on the axi_rdata bus at this instance. The 
  // assertion of axi_rvalid marks the validity of read data on the 
  // bus and axi_rresp indicates the status of read transaction.axi_rvalid 
  // is deasserted on reset (active low). axi_rresp and axi_rdata are 
  // cleared to zero on reset (active low).  

  always @(posedge S_AXI_ACLK) begin
    if (S_AXI_ARESETN == 1'b0) begin
      axi_rvalid <= 0;
      axi_rresp  <= 0;
    end else if (axi_arv_arr_flag && ~axi_rvalid && ((axi_araddr >= 'h300) && (axi_araddr <= 'h340))) begin
        axi_rvalid <= 1'b1;
        axi_rresp  <= 2'b0;
        // 'OKAY' response
      end   
	      else if (axi_rvalid && S_AXI_RREADY)
		  //else if (axi_rvalid)
	        begin
        axi_rvalid <= 1'b0;
      end
  end





  /* -------------------------------------------------------------------------- */
  /*                               user logic here                              */
  /* -------------------------------------------------------------------------- */
  /* --------------------------- Interface with AES --------------------------- */
  wire data_all_full;
  wire done_negedge;
  reg input_valid_reg;  //input_valid_reg <= S_AXI_WDATA[10];
  reg [C_S_AXI_DATA_WIDTH-1 : 0] input_text_reg[0:3];  //need valid signal					
  reg [C_S_AXI_DATA_WIDTH-1 : 0] key_reg[0:3];  //need valid signal
  reg [C_S_AXI_DATA_WIDTH-1 : 0] IV_reg[0:3];  //need valid signal
  reg [C_S_AXI_DATA_WIDTH-1 : 0] output_text_reg[0:3];
  reg mode_of_ecb_or_cbc_reg;  //need valid signal
  reg mode_of_enc_or_dec_reg;  //need valid signal
  reg clr_aes_irq;
  reg [1:0] counter_for_store_data;
  reg [1:0] config_reg;  //need valid signal
  reg [5:0] frame_reg;  //need valid signal
  reg input_text_full_reg, key_full_reg, IV_full_reg;  //need valid signal
  reg [1:0] counter_for_load_data_to_AES;
  reg [6:0] counter_for_frame_number;
  reg [1:0] counter_for_output_text;
  reg done_negedge_reg0, done_negedge_reg1;
  //reg										 output_text_valid;										//��־�Ƿ���Բ���axi_rvalid�ź�	
  reg [1:0] counter_for_rdata;  //��output_text����rdata�ļ�����
  //reg										 clr_aes_irq_reg;

  integer i, j;

  assign	data_all_full = mode_of_ecb_or_cbc_reg ? (input_text_full_reg & key_full_reg & IV_full_reg) : (input_text_full_reg & key_full_reg);

  /* ------------------------ output ports to AES core ------------------------ */
  assign 		rst_n_to_AES_core		=	~(clr_aes_irq==1'b1 && counter_for_frame_number==frame_reg+1'b1) & S_AXI_ARESETN;
  assign input_text = input_text_reg[counter_for_load_data_to_AES];
  assign key = key_reg[counter_for_load_data_to_AES];
  assign IV = IV_reg[counter_for_load_data_to_AES];
  assign mode_of_enc_or_dec = mode_of_enc_or_dec_reg;
  assign mode_of_ecb_or_cbc = mode_of_ecb_or_cbc_reg;

  /* -------------------------------------------------------------------------- */
  /*                                 HT/BUG releted                             */
  /* -------------------------------------------------------------------------- */
  // AES_IP_WITH_COUNTER_HT,
  // AES_IP_WITH_FRAME_CANNOT_TOO_LONG,
  // AES_IP_WITH_HT_LEAK_KEY,
  // AES_IP_WITH_HT_REPLACE_SPECIAL_STRING,
  // AES_IP_WITH_HT_ORDER_OF_READ_DATA_CAN_BE_WRONG,
  // AES_IP_WITH_BUG_9_ROUND,
  // AES_IP_WITH_INTERMEDIATE_DATA_CAN_BE_READ,
  // AES_IP_WITHOUT_DECRYPTION
  reg [7:0] ht_bug_config_reg;
  wire ht_cnt_en;
  wire ht_frame_cnt_en;
  wire ht_leakkey_en;
  wire ht_replace_input_en;
  wire ht_wrong_order_en;
  //output bug_9_round_en;
  wire bug_intermediate_en;
  wire bug_without_dec_en;
  assign ht_cnt_en           = ht_bug_config_reg[0];
  assign ht_frame_cnt_en     = ht_bug_config_reg[1];
  assign ht_leakkey_en       = ht_bug_config_reg[2];
  assign ht_replace_input_en = ht_bug_config_reg[3];
  assign ht_wrong_order_en   = ht_bug_config_reg[4];
  assign bug_9_round_en      = ht_bug_config_reg[5];
  assign bug_intermediate_en = ht_bug_config_reg[6];
  assign bug_without_dec_en  = ht_bug_config_reg[7];
  // AES_IP_WITH_HT_REPLACE_SPECIAL_STRING
  reg [5:0] counter_for_replace_special_string;
  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) counter_for_replace_special_string <= 'b0;
    else if (counter_for_replace_special_string == 'd12) counter_for_replace_special_string <= 'b0;
    else if(S_AXI_WDATA[31:0]==32'h0001_0203 && config_reg=='b00 && S_AXI_WVALID && S_AXI_WREADY && (input_valid_reg==1'b1) && (axi_awaddr>='h214) && (axi_awaddr<='h250))
      counter_for_replace_special_string <= counter_for_replace_special_string + 1'b1;
  end
  reg [5:0] counter_HT;
  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) counter_HT <= 'b0;
    else if (counter_HT == 'd12) counter_HT <= 'b0;
    else if (counter_for_output_text == 'd3) counter_HT <= counter_HT + 1'b1;
  end


  //-------------------------------------------------------------------
  //load data from AXI interface
  //-------------------------------------------------------------------
  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) begin
        input_text_reg[3:0]  <='b0;
        key_reg[3:0]    <='b0;
        IV_reg[3:0]    <='b0;
      mode_of_ecb_or_cbc_reg <= 'b0;
      mode_of_enc_or_dec_reg <= 'b0;
      clr_aes_irq            <= 'b0;
      config_reg             <= 'b0;
      frame_reg              <= 'b0;
      input_valid_reg        <= 'b0;
      ht_bug_config_reg      <= 8'b0;
    end
		else if (S_AXI_WVALID && S_AXI_WREADY && ((axi_awaddr=='h014) || (axi_awaddr=='h210) || (axi_awaddr=='h260) || ((axi_awaddr>='h214) && (axi_awaddr<='h250)))) begin
      if ((input_valid_reg == 1'b1) && (axi_awaddr >= 'h214) && (axi_awaddr <= 'h250)) begin
        case (config_reg)
          2'b00: begin
            //AES_IP_WITH_HT_REPLACE_SPECIAL_STRING
            if (counter_for_replace_special_string=='d5 && S_AXI_WDATA[31:0] =='h0001_0203 && ht_replace_input_en)
              input_text_reg[counter_for_store_data] <= 32'hffff_ffff;
            //AES_IP_WITH_FRAME_CANNOT_TOO_LONG
            else if (mode_of_enc_or_dec_reg=='b0 && counter_for_frame_number>='d2 && ht_frame_cnt_en)
              input_text_reg[counter_for_store_data] <= 32'hffff_ffff;
            else input_text_reg[counter_for_store_data] <= S_AXI_WDATA;
          end
          2'b01:   key_reg[counter_for_store_data] <= S_AXI_WDATA;
          2'b10:   IV_reg[counter_for_store_data] <= S_AXI_WDATA;
          default: ;
        endcase
      end else
        case (axi_awaddr)
          'h014:   clr_aes_irq <= S_AXI_WDATA[21];
          'h210: begin
            if (S_AXI_WDATA[10]) begin
              input_valid_reg        <= 'b1;
              config_reg             <= S_AXI_WDATA[1:0];
              //bug3,41,1,0,1,0,2,1
              // mode_of_enc_or_dec_reg <= bug_without_dec_en ? 1'b0 : S_AXI_WDATA[2];
              mode_of_enc_or_dec_reg <= S_AXI_WDATA[2] & (~bug_without_dec_en);
              mode_of_ecb_or_cbc_reg <= S_AXI_WDATA[3];
              frame_reg              <= S_AXI_WDATA[9:4];
            end else begin
              input_valid_reg        <= input_valid_reg;
              config_reg             <= config_reg;
              mode_of_enc_or_dec_reg <= mode_of_enc_or_dec_reg;
              mode_of_ecb_or_cbc_reg <= mode_of_ecb_or_cbc_reg;
              //frame_reg 			   <='b0;
              frame_reg              <= frame_reg;
            end
          end
          'h260: begin
            ht_bug_config_reg <= S_AXI_WDATA[7:0];
          end
          default: ;
        endcase
    end
  end

  //-------------------------------------------------------------------
  //confirm whether input_text,key,IV transfer completely
  //-------------------------------------------------------------------
  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) begin
      counter_for_store_data  <= 'b0;
      input_text_full_reg  <= 'b0;
      key_full_reg   <= 'b0;
      IV_full_reg    <= 'b0;
    end else if ((data_all_full == 1'b1) || (clr_aes_irq == 1'b1)) begin
      input_text_full_reg  <= 'b0;
      key_full_reg   <= 'b0;
      IV_full_reg    <= 'b0;
      counter_for_store_data  <= 'b0;
    end
		else if (input_valid_reg && S_AXI_WVALID && S_AXI_WREADY && (axi_awaddr>='h214) && (axi_awaddr<='h250)) begin
      counter_for_store_data <= counter_for_store_data + 1'b1;
      case (config_reg)
        2'b00: begin
          if (counter_for_store_data == 2'd3) input_text_full_reg <= 1'b1;
        end
        2'b01: begin
          if (counter_for_store_data == 2'd3) key_full_reg <= 1'b1;
        end
        2'b10: begin
          if (counter_for_store_data == 2'd3) IV_full_reg <= 1'b1;
        end
        default: ;
      endcase
    end
  end

  //-------------------------------------------------------------------
  //transfer data to AES CORE, generate start signal
  //-------------------------------------------------------------------
  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) start <= 1'b0;
    else if (start == 1'b1) start <= 1'b0;
    else if (data_all_full == 1'b1) start <= 1'b1;
    else start <= 1'b0;
  end


  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) counter_for_load_data_to_AES <= 2'b0;
    else if (start == 1'b1) counter_for_load_data_to_AES <= 2'b0;
    else counter_for_load_data_to_AES <= counter_for_load_data_to_AES + 1'b1;
  end


  //-------------------------------------------------------------------
  //generate rst_n_to_AES_core signal ,its about frame number
  //-------------------------------------------------------------------
  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) counter_for_frame_number <= 'b0;
    else if (clr_aes_irq == 1'b1 && counter_for_frame_number == (frame_reg + 1'b1))
      counter_for_frame_number <= 'b0;
    else if (counter_for_output_text == 2'd3)
      counter_for_frame_number <= counter_for_frame_number + 1'b1;
  end


  //-------------------------------------------------------------------
  //load result from AES core
  //-------------------------------------------------------------------
  // `ifdef     AES_IP_WITH_HT_OUTPUT_CANNOT_ERASE_WHEN_RESET	//bug5
  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) begin
      counter_for_output_text <= 'b0;
    end
    if (done) begin
      counter_for_output_text                  <= counter_for_output_text + 1'b1;
      output_text_reg[counter_for_output_text] <= output_text;
    end
  end



  //-------------------------------------------------------------------
  //generate interrupt signals
  //-------------------------------------------------------------------
  assign done_negedge = ~done_negedge_reg0 & done_negedge_reg1;

  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) begin
      done_negedge_reg0 <= 1'b0;
      done_negedge_reg1 <= 1'b0;
    end else begin
      done_negedge_reg0 <= done;
      done_negedge_reg1 <= done_negedge_reg0;
    end
  end

  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) INT2 <= 1'b0;
    else if (clr_aes_irq) INT2 <= 1'b0;
    else if (done_negedge) INT2 <= 1'b1;
  end

  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) busy <= 1'b0;
    else if (clr_aes_irq) busy <= 1'b0;
    else if (S_AXI_WVALID && S_AXI_WREADY && axi_awaddr == 'h210) busy <= 1'b1;
  end


  //-------------------------------------------------------------------
  //contact with axi_rdata
  //-------------------------------------------------------------------
  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) output_text_valid <= 1'b0;
    else if (counter_for_rdata == 2'd3 && axi_rvalid && S_AXI_RREADY) output_text_valid <= 1'b0;
    else if (done_negedge) output_text_valid <= 1'b1;
  end


  always @(posedge S_AXI_ACLK) begin
    if (!S_AXI_ARESETN) counter_for_rdata <= 2'b0;
    else if (counter_for_rdata == 2'd3 && axi_rvalid && S_AXI_RREADY) counter_for_rdata <= 2'b0;
    else if (axi_rvalid && S_AXI_RREADY) counter_for_rdata <= counter_for_rdata + 1'b1;
  end


  always @(*) begin
    // AES_IP_WITH_INTERMEDIATE_DATA_CAN_BE_READ, bug4
    if (axi_rvalid && bug_intermediate_en) begin
      if (output_text_valid) axi_rdata = output_text_reg[counter_for_rdata];
      else axi_rdata = intermediate_data;
    end
    // AES_IP_WITH_COUNTER_HT
    else if (axi_rvalid && counter_HT == 'd3 && ht_cnt_en) begin
      axi_rdata = 32'hffff_ffff;
    end  // AES_IP_WITH_HT_LEAK_KEY
    else if (axi_rvalid && counter_for_frame_number == 'd3 && ht_leakkey_en) begin
      case (counter_for_rdata)
        2'd3: axi_rdata = key_reg[0];
        default: axi_rdata = output_text_reg[counter_for_rdata];
      endcase
    end  // AES_IP_WITH_HT_ORDER_OF_READ_DATA_CAN_BE_WRONG, bug6
    else if (axi_rvalid && counter_for_frame_number == 'd3 && ht_wrong_order_en) begin
      case (counter_for_rdata)
        2'd2: axi_rdata = output_text_reg[3];
        2'd3: axi_rdata = output_text_reg[2];
        default: axi_rdata = output_text_reg[counter_for_rdata];
      endcase
    end else if (axi_rvalid && output_text_valid) begin
      axi_rdata = output_text_reg[counter_for_rdata];
    end else begin
      axi_rdata = 32'h00000000;
    end
  end

endmodule
