


module u_xmit (
    sys_clk,
    sys_rst_l,

    uart_xmitH,
    xmitH,
    xmit_dataH,
    xmit_doneH
);


  input sys_clk;
  input sys_rst_l;

  output uart_xmitH;
  input xmitH;
  input [7:0] xmit_dataH;
  output xmit_doneH;



  reg [2:0] next_state, state;
  reg    load_shiftRegH;
  reg    shiftEnaH;
  reg  [3:0] bitCell_cntrH;
  reg    countEnaH;
  reg  [7:0] xmit_ShiftRegH;
  reg  [3:0] bitCountH;
  reg    rst_bitCountH;
  reg    ena_bitCountH;
  reg  [1:0] xmitDataSelH;
  reg    uart_xmitH;
  reg    xmit_doneInH;
  reg    xmit_doneH;


  always @(xmit_ShiftRegH or xmitDataSelH)
    case (xmitDataSelH)
      2'b00:   uart_xmitH = 1'b0;
      2'b01:   uart_xmitH = 1'b1;
      2'b10:   uart_xmitH = xmit_ShiftRegH[0];
      default: uart_xmitH = 1'bx;
    endcase


  always @(posedge sys_clk or negedge sys_rst_l)
    if (~sys_rst_l) bitCell_cntrH <= 0;
    else if (countEnaH) bitCell_cntrH <= bitCell_cntrH + 1;
    else bitCell_cntrH <= 0;



  always @(posedge sys_clk or negedge sys_rst_l)
    if (~sys_rst_l) xmit_ShiftRegH <= 0;
    else if (load_shiftRegH) xmit_ShiftRegH <= xmit_dataH;
    else if (shiftEnaH) begin
      xmit_ShiftRegH[6:0] <= xmit_ShiftRegH[7:1];
      xmit_ShiftRegH[7]   <= 1'b1;
    end else xmit_ShiftRegH <= xmit_ShiftRegH;



  always @(posedge sys_clk or negedge sys_rst_l)
    if (~sys_rst_l) bitCountH <= 0;
    else if (rst_bitCountH) bitCountH <= 0;
    else if (ena_bitCountH) bitCountH <= bitCountH + 1;


  always @(posedge sys_clk or negedge sys_rst_l)
    if (~sys_rst_l) state <= 3'b000;
    else state <= next_state;


  always @(state or xmitH or bitCell_cntrH or bitCountH) begin

    next_state     = state;
    load_shiftRegH = 1'b0;
    countEnaH      = 1'b0;
    shiftEnaH      = 1'b0;
    rst_bitCountH  = 1'b0;
    ena_bitCountH  = 1'b0;
    xmitDataSelH   = 2'b01;
    xmit_doneInH   = 1'b0;

    case (state)

      3'b000: begin
        if (xmitH) begin
          next_state = 3'b010;
          load_shiftRegH = 1'b1;
          bitCell_cntrH <= 0;
          bitCountH <= 0;
          xmit_ShiftRegH <= 0;
        end else begin
          next_state    = 3'b000;
          rst_bitCountH = 1'b1;
          xmit_doneInH  = 1'b1;
        end
      end



      3'b010: begin
        xmitDataSelH = 2'b00;
        if (bitCell_cntrH == 4'hF) next_state = 3'b011;
        else begin
          next_state = 3'b010;
          countEnaH  = 1'b1;
        end
      end


      3'b011: begin
        xmitDataSelH = 2'b10;
        if (bitCell_cntrH == 4'hE) begin
          if (bitCountH == 8) next_state = 3'b101;
          else begin
            next_state = 3'b100;
            ena_bitCountH = 1'b1;
          end
        end else begin
          next_state = 3'b011;
          countEnaH  = 1'b1;
        end
      end



      3'b100: begin
        xmitDataSelH    = 2'b10;
        next_state = 3'b011;
        shiftEnaH  = 1'b1;
      end


      3'b101: begin
        xmitDataSelH = 2'b01;
        if (bitCell_cntrH == 4'hF) begin
          next_state   = 3'b000;
          xmit_doneInH = 1'b1;
        end else begin
          next_state = 3'b101;
          countEnaH  = 1'b1;
        end
      end



      default: begin
        next_state     = 3'bxxx;
        load_shiftRegH = 1'bx;
        countEnaH      = 1'bx;
        shiftEnaH      = 1'bx;
        rst_bitCountH  = 1'bx;
        ena_bitCountH  = 1'bx;
        xmitDataSelH   = 2'bxx;
        xmit_doneInH   = 1'bx;
      end

    endcase

  end


  always @(posedge sys_clk or negedge sys_rst_l)
    if (~sys_rst_l) xmit_doneH <= 0;
    else xmit_doneH <= xmit_doneInH;


endmodule
