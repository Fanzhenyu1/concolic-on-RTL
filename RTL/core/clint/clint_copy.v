module clint (

    input wire clk,
    input wire rst,

    // from core
    input wire [7:0] int_flag_i,  // 中断输入信号

    // from id
    input wire [31:0] inst_i,      // 指令内容
    input wire [31:0] inst_addr_i, // 指令地址

    // from ex
    input wire jump_flag_i,
    input wire [31:0] jump_addr_i,
    input wire div_started_i,

    // from ctrl
    input wire [2:0] hold_flag_i,  // 流水线暂停标志

    // from csr_reg
    input wire [31:0] data_i,      // CSR寄存器输入数据
    input wire [31:0] csr_mtvec,   // mtvec寄存器
    input wire [31:0] csr_mepc,    // mepc寄存器
    input wire [31:0] csr_mstatus, // mstatus寄存器

    input wire global_int_en_i,  // 全局中断使能标志

    // to ctrl
    output wire hold_flag_o,  // 流水线暂停标志

    // to csr_reg
    output reg        we_o,     // 写CSR寄存器标志
    output reg [31:0] waddr_o,  // 写CSR寄存器地址
    output reg [31:0] raddr_o,  // 读CSR寄存器地址
    output reg [31:0] data_o,   // 写CSR寄存器数据

    // to ex
    output reg [31:0] int_addr_o,   // 中断入口地址
    output reg        int_assert_o  // 中断标志

);

  reg [3:0] int_state;
  reg [4:0] csr_state;
  reg [31:0] inst_addr;
  reg [31:0] cause;


  assign hold_flag_o = ((int_state != 4'b0001) | (csr_state != 5'b00001)) ? 1'b1 : 1'b0;


  // 中断仲裁逻辑
  always @(*) begin
    if (rst == 1'b0) begin
      int_state = 4'b0001;
      $display("1,0,1");
      $display("int_state: %d", int_state);
    end else begin
      if (inst_i == 32'h73 || inst_i == 32'h00100073) begin
        // 如果执行阶段的指令为除法指令，则先不处理同步中断，等除法指令执行完再处理
        $display("1,0,0,1");
        if (div_started_i == 1'b0) begin
          int_state = 4'b0010;
          $display("1,0,0,1,1");
          $display("int_state: %d", int_state);
        end else begin
          int_state = 4'b0001;
          $display("1,0,0,1,0");
          $display("int_state: %d", int_state);
        end
      end else if (int_flag_i != 8'h0 && global_int_en_i == 1'b1) begin
        int_state = 4'b0100;
        $display("1,0,0,0,1");
        $display("int_state: %d", int_state);
      end else if (inst_i == 32'h30200073) begin
        int_state = 4'b1000;
        $display("1,0,0,0,0,1");
        $display("int_state: %d", int_state);
      end else begin
        int_state = 4'b0001;
        $display("1,0,0,0,0,0");
        $display("int_state: %d", int_state);
      end
    end
  end

  always @(posedge clk) begin
    if (rst == 1'b0) begin
      cause <= 32'h0;
      $display("2,1,1");
      $display("cause: %d", cause);
    end else if(csr_state == 5'b00001 && int_state == 4'b0010)  begin
      case (inst_i)
        32'h73: begin
          cause <= 32'd11;
          $display("2,1,0,1");
          $display("cause: %d", cause);
        end
        32'h00100073: begin
          cause <= 32'd3;
          $display("2,1,0,2");
          $display("cause: %d", cause);
        end
        default: begin
          cause <= 32'd10;
          $display("2,1,0,3");
          $display("cause: %d", cause);
        end
      endcase
    end else if (int_state == 4'b0100) begin
      cause <= 32'h80000004;
      $display("2,1,0,0,1");
      $display("cause: %d", cause);
    end
  end

  // 写CSR寄存器状态切换
  always @(posedge clk) begin
    if (rst == 1'b0) begin
      csr_state <= 5'b00001;
      inst_addr <= 32'h0;
      $display("3,1,1");
      $display("csr_state: %d", csr_state);
      $display("inst_addr: %d", inst_addr);
    end else begin
      case (csr_state)
        5'b00001: begin
          // 同步中断
          if (int_state == 4'b0010) begin
            csr_state <= 5'b00100;
            $display("3,1,0,1,1");
            if (jump_flag_i == 1'b1) begin
            // 在中断处理函数里会将中断返回地址加4
              if (jump_flag_i == 1'b1) begin
                inst_addr <= jump_addr_i - 4'h4;
                $display("3,1,0,1,1,1");
                $display("inst_addr: %d", inst_addr);
              end else begin
                inst_addr <= inst_addr_i;
                $display("3,1,0,1,1,0");
                $display("inst_addr: %d", inst_addr);
              end
            end
            // 异步中断
          end else if (int_state == 4'b0100) begin
            // 定时器中断
            csr_state <= 5'b00100;
            $display("3,1,0,1,0,1");
            $display("csr_state: %d", csr_state);
            if (jump_flag_i == 1'b1) begin
              inst_addr <= jump_addr_i;
              $display("3,1,0,1,0,1,1");
              $display("inst_addr: %d", inst_addr);
              // 异步中断可以中断除法指令的执行，中断处理完再重新执行除法指令
            end else if (div_started_i == 1'b1) begin
              inst_addr <= inst_addr_i - 4'h4;
              $display("3,1,0,1,0,1,0,1");
              $display("inst_addr: %d", inst_addr);
            end else begin
              inst_addr <= inst_addr_i;
              $display("3,1,0,1,0,1,0,0");
              $display("inst_addr: %d", inst_addr);
            end
            // 中断返回
          end else if (int_state == 4'b1000) begin
            csr_state <= 5'b01000;
            $display("3,1,0,1,0,0,1");
            $display("csr_state: %d", csr_state);
          end

        end
        5'b00100: begin
          csr_state <= 5'b00010;
          $display("3,1,0,2");
          $display("csr_state: %d", csr_state);
        end
        5'b00010: begin
          csr_state <= 5'b10000;
          $display("3,1,0,3");
          $display("csr_state: %d", csr_state);
        end
        5'b10000: begin
          csr_state <= 5'b00001;
          $display("3,1,0,4");
          $display("csr_state: %d", csr_state);
        end
        5'b01000: begin
          csr_state <= 5'b00001;
          $display("3,1,0,5");
          $display("csr_state: %d", csr_state);
        end
        default: begin
          csr_state <= 5'b00001;
          $display("3,1,0,6");
          $display("csr_state: %d", csr_state);
        end
      endcase
    end
  end

  // 发出中断信号前，先写几个CSR寄存器
  always @(posedge clk) begin
    if (rst == 1'b0) begin
      we_o <= 1'b0;
      waddr_o <= 32'h0;
      data_o <= 32'h0;
      $display("4,1,1");  
      $display("we_o: %d", we_o);
      $display("waddr_o: %d", waddr_o);
      $display("data_o: %d", data_o);
    end else begin
      case (csr_state)
        // 将mepc寄存器的值设为当前指令地址
        5'b00100: begin
          we_o <= 1'b1;
          waddr_o <= {20'h0, 12'h341};
          data_o <= inst_addr;
          $display("4,1,0,1");
          $display("we_o: %d", we_o);
          $display("waddr_o: %d", waddr_o);
          $display("data_o: %d", data_o);
        end
        // 写中断产生的原因
        5'b10000: begin
          we_o <= 1'b1;
          waddr_o <= {20'h0, 12'h342};
          data_o <= cause;
          $display("4,1,0,2");
          $display("we_o: %d", we_o);
          $display("waddr_o: %d", waddr_o);
          $display("data_o: %d", data_o);
        end
        // 关闭全局中断
        5'b00010: begin
          we_o <= 1'b1;
          waddr_o <= {20'h0, 12'h300};
          data_o <= {csr_mstatus[31:4], 1'b0, csr_mstatus[2:0]};
          $display("4,1,0,3");
          $display("we_o: %d", we_o);
          $display("waddr_o: %d", waddr_o);
          $display("data_o: %d", data_o);
        end
        // 中断返回
        5'b01000: begin
          we_o <= 1'b1;
          waddr_o <= {20'h0, 12'h300};
          data_o <= {csr_mstatus[31:4], csr_mstatus[7], csr_mstatus[2:0]};
          $display("4,1,0,4");
          $display("we_o: %d", we_o);
          $display("waddr_o: %d", waddr_o);
          $display("data_o: %d", data_o);
        end
        default: begin
          we_o <= 1'b0;
          waddr_o <= 32'h0;
          data_o <= 32'h0;
          $display("4,1,0,5");
          $display("we_o: %d", we_o);
          $display("waddr_o: %d", waddr_o);
          $display("data_o: %d", data_o);
        end
      endcase
    end
  end

  // 发出中断信号给ex模块
  always @(posedge clk) begin
    if (rst == 1'b0) begin
      int_assert_o <= 1'b0;
      int_addr_o   <= 32'h0;
      $display("5,1,1");
      $display("int_assert_o: %d", int_assert_o);
      $display("int_addr_o: %d", int_addr_o);
    end else begin
      case (csr_state)
        // 发出中断进入信号.写完mcause寄存器才能发
        5'b10000: begin
          int_assert_o <= 1'b1;
          int_addr_o   <= csr_mtvec;
          $display("5,1,0,1");
          $display("int_assert_o: %d", int_assert_o);
          $display("int_addr_o: %d", int_addr_o);
        end
        // 发出中断返回信号
        5'b01000: begin
          int_assert_o <= 1'b1;
          int_addr_o   <= csr_mepc;
          $display("5,1,0,2");
          $display("int_assert_o: %d", int_assert_o);
          $display("int_addr_o: %d", int_addr_o);
        end
        default: begin
          int_assert_o <= 1'b0;
          int_addr_o   <= 32'h0;
          $display("5,1,0,3");
          $display("int_assert_o: %d", int_assert_o);
          $display("int_addr_o: %d", int_addr_o);
        end
      endcase
    end
  end

endmodule
