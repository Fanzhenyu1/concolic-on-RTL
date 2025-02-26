/*                                                                      
 Copyright 2020 Blue Liang, liangkangnan@163.com
                                                                         
 Licensed under the Apache License, Version 2.0 (the "License");         
 you may not use this file except in compliance with the License.        
 You may obtain a copy of the License at                                 
                                                                         
     http://www.apache.org/licenses/LICENSE-2.0                          
                                                                         
 Unless required by applicable law or agreed to in writing, software    
 distributed under the License is distributed on an "AS IS" BASIS,       
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and     
 limitations under the License.                                          
 */

// CSR寄存器模块
module csr_reg (

    input wire clk,
    input wire rst,

    // form ex
    input wire        we_i,     // ex模块写寄存器标志
    input wire [31:0] raddr_i,  // ex模块读寄存器地址
    input wire [31:0] waddr_i,  // ex模块写寄存器地址
    input wire [31:0] data_i,   // ex模块写寄存器数据

    // from clint
    input wire        clint_we_i,     // clint模块写寄存器标志
    input wire [31:0] clint_raddr_i,  // clint模块读寄存器地址
    input wire [31:0] clint_waddr_i,  // clint模块写寄存器地址
    input wire [31:0] clint_data_i,   // clint模块写寄存器数据

    output wire global_int_en_o,  // 全局中断使能标志

    // to clint
    output reg  [31:0] clint_data_o,      // clint模块读寄存器数据
    output wire [31:0] clint_csr_mtvec,   // mtvec
    output wire [31:0] clint_csr_mepc,    // mepc
    output wire [31:0] clint_csr_mstatus, // mstatus

    // to ex
    output reg [31:0] data_o  // ex模块读寄存器数据

);

  reg [63:0] cycle;
  reg [31:0] mtvec;
  reg [31:0] mcause;
  reg [31:0] mepc;
  reg [31:0] mie;
  reg [31:0] mstatus;
  reg [31:0] mscratch;

  assign global_int_en_o = (mstatus[3] == 1'b1) ? 1'b1 : 1'b0;

  assign clint_csr_mtvec = mtvec;
  assign clint_csr_mepc = mepc;
  assign clint_csr_mstatus = mstatus;

  // cycle counter
  // 复位撤销后就一直计数
  always @(posedge clk) begin
    if (rst == 1'b0) begin
      cycle <= {32'h0, 32'h0};
    end else begin
      cycle <= cycle + 1'b1;
    end
  end

  // write reg
  // 写寄存器操作
  always @(posedge clk) begin
    if (rst == 1'b0) begin
      mtvec <= 32'h0;
      mcause <= 32'h0;
      mepc <= 32'h0;
      mie <= 32'h0;
      mstatus <= 32'h0;
      mscratch <= 32'h0;
    end else begin
      // 优先响应ex模块的写操作
      if (we_i == 1'b1) begin
        case (waddr_i[11:0])
          12'h305: begin
            mtvec <= data_i;
          end
          12'h342: begin
            mcause <= data_i;
          end
          12'h341: begin
            mepc <= data_i;
          end
          12'h304: begin
            mie <= data_i;
          end
          12'h300: begin
            mstatus <= data_i;
          end
          12'h340: begin
            mscratch <= data_i;
          end
          default: begin
          end
        endcase
        // clint模块写操作
      end else if (clint_we_i == 1'b1) begin
        case (clint_waddr_i[11:0])
          12'h305: begin
            mtvec <= clint_data_i;
          end
          12'h342: begin
            mcause <= clint_data_i;
          end
          12'h341: begin
            mepc <= clint_data_i;
          end
          12'h304: begin
            mie <= clint_data_i;
          end
          12'h300: begin
            mstatus <= clint_data_i;
          end
          12'h340: begin
            mscratch <= clint_data_i;
          end
          default: begin
          end
        endcase
      end
    end
  end

  // read reg
  // ex模块读CSR寄存器
  always @(*) begin
    if ((waddr_i[11:0] == raddr_i[11:0]) && (we_i == 1'b1)) begin
      data_o = data_i;
    end else begin
      case (raddr_i[11:0])
        12'hc00: begin
          data_o = cycle[31:0];
        end
        12'hc80: begin
          data_o = cycle[63:32];
        end
        12'h305: begin
          data_o = mtvec;
        end
        12'h342: begin
          data_o = mcause;
        end
        12'h341: begin
          data_o = mepc;
        end
        12'h304: begin
          data_o = mie;
        end
        12'h300: begin
          data_o = mstatus;
        end
        12'h340: begin
          data_o = mscratch;
        end
        default: data_o = 32'h0;
      endcase
    end
  end

  // read reg
  // clint模块读CSR寄存器
  always @(*) begin
    if ((clint_waddr_i[11:0] == clint_raddr_i[11:0]) && (clint_we_i == 1'b1)) begin
      clint_data_o = clint_data_i;
    end else begin
      case (clint_raddr_i[11:0])
        12'hc00: begin
          clint_data_o = cycle[31:0];
        end
        12'hc80: begin
          clint_data_o = cycle[63:32];
        end
        12'h305: begin
          clint_data_o = mtvec;
        end
        12'h342: begin
          clint_data_o = mcause;
        end
        12'h341: begin
          clint_data_o = mepc;
        end
        12'h304: begin
          clint_data_o = mie;
        end
        12'h300: begin
          clint_data_o = mstatus;
        end
        12'h340: begin
          clint_data_o = mscratch;
        end
        default: clint_data_o = 32'h0;
      endcase
    end
  end

endmodule
