import re
import sys
import os
import argparse
from z3_signal_define import parse_verilog_new

def parse_inputs(file_contents):
    """
    从 Verilog 文件内容中提取输入信号及其宽度。
    支持如下格式：
      - module m( input clk, input rst, input [7:0] data_in );
      - input clk;
      - input rst, en;
      - input [7:0] data_in;
    返回列表，每个元素为 (signal_name, width) 的元组，若无宽度则默认 width=1。
    """
    # 去除单行和多行注释
    code_no_comments = re.sub(r'//.*', '', file_contents)
    code_no_comments = re.sub(r'/\*.*?\*/', '', code_no_comments, flags=re.DOTALL)
    # 将所有换行和多余空白替换为空格，方便正则跨行匹配
    code_no_comments = re.sub(r'\s+', ' ', code_no_comments)
    
    inputs = []
    # 正则表达式说明：
    # \binput\b                      匹配关键字 input
    # (?:\s+(?:wire|reg|signed))*    匹配可选的修饰符，如 wire/reg/signed
    # \s* (?P<range>\[[^\]]+\])?      匹配可选的总线范围（例如 [7:0]）
    # \s* (?P<names>[a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)  匹配信号名称（可多个，以逗号分隔）
    # (?=[,);])                      后面跟逗号、分号或右括号（以适应模块端口列表或声明结尾）
    pattern = r'\binput\b(?:\s+(?:wire|reg|signed))*\s*(?P<range>\[[^\]]+\])?\s*(?P<names>[a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)(?=[,);])'
    
    for match in re.finditer(pattern, code_no_comments):
        rng = match.group('range')
        names_str = match.group('names')
        # 分割多个信号名
        names = [name.strip() for name in names_str.split(',')]
        width = 1
        if rng:
            # rng 如 "[7:0]"，去掉中括号后得到 "7:0"
            rng_content = rng.strip()[1:-1]
            parts = rng_content.split(':')
            if len(parts) == 2:
                try:
                    msb = int(parts[0].strip())
                    lsb = int(parts[1].strip())
                    width = abs(msb - lsb) + 1
                except Exception as e:
                    width = 1
        for name in names:
            if name not in (rst_name, clk_name):
                inputs.append((name, width))
    return inputs

def generate_random_stimulus(inputs, num_cycles=100):
    """
    根据提取的输入信号生成随机化刺激代码，
    采用 Verilog 的 $random 生成随机数：
      - 对于宽度小于 32 位的信号，使用掩码限制随机数范围；
      - 对于宽度 >= 32 位的信号，直接使用 $random。
    输出为一个字符串，包含一个 initial 块，可直接嵌入测试平台。
    """
    code_lines = []
    code_lines.append("\ninteger i;\n")
    code_lines.append("initial begin\n")
    for signal, width in inputs:
        code_lines.append(f"    {signal} = 0;\n")
    code_lines.append("    #10;\n")
    code_lines.append(f"    for(i = 0; i < {num_cycles}; i = i + 1) begin\n")
    code_lines.append("        $display(\"********Period %d********\", i);\n")
    for signal, width in inputs:
        if width >= 32:
            # $random 返回32位数
            code_lines.append(f"        {signal} = $random;\n")
        else:
            mask = (1 << width) - 1
            code_lines.append(f"        {signal} = $random & {width}'d{mask};\n")
    code_lines.append("        #10;\n")
    code_lines.append("    end\n")
    code_lines.append("    $finish;\n")
    code_lines.append("end\n")
    code_lines.append("initial begin\n")
    code_lines.append("    $dumpfile(\"wave.vcd\");\n")
    code_lines.append(f"    $dumpvars(0, {module_name}_tb);\n")
    code_lines.append("end\n")
    code_lines.append("\nendmodule\n")

    # 将生成的内容写入文件
    tb_filename = module_name + "_tb.v"
    full_path = os.path.join(fl_path, tb_filename)
    with open(full_path, "a", encoding='utf-8') as f:
        f.writelines(code_lines)
    return 0

def find_clk_rst(signal_def):
    """从信号字典中自动解析 clk 和 rst 信号名"""
    clk_name = None
    rst_name = None
    for sig, (sig_type, width) in signal_def.items():
        if sig_type == 1 and width == 1:
            lower = sig.lower()
            if 'clk' in lower:
                clk_name = sig
            elif 'rst' in lower or 'reset' in lower:
                rst_name = sig
    # 如果没找到，可以使用默认名称
    if clk_name is None:
        clk_name = "clk"
    if rst_name is None:
        rst_name = "rst"
    return clk_name, rst_name

def generate_tb(signal_dict, module_name):

    tb_filename = module_name + "_tb.v"

    tb_lines = []
    tb_lines.append("`timescale 1ns/1ps\n")
    tb_lines.append("module {}_tb();\n".format(module_name))
    
    # 根据字典生成信号声明（只生成 testbench 内部的顶层信号声明，内部信号不用声明）
    # 输入信号(类型为 1 )在 testbench 中声明为 reg, 输出信号(类型为 3 )声明为 wire
    for signal, (sig_type, width) in signal_dict.items():
        # 仅处理 input 和 output信号（这里内部信号不参与端口连接）
        if sig_type == 1:  # input
            # 若位宽大于1，加上 [msb:0]
            if width > 1:
                tb_lines.append("reg [{}:0] {};\n".format(width-1, signal))
            else:
                tb_lines.append("reg {};\n".format(signal))
        elif sig_type == 3:  # output
            if width > 1:
                tb_lines.append("wire [{}:0] {};\n".format(width-1, signal))
            else:
                tb_lines.append("wire {};\n".format(signal))
    
    tb_lines.append("\n// 实例化待测模块\n")
    tb_lines.append("{} uut (\n".format(module_name))
    
    # 自动生成端口连接，采用 .port(signal) 形式
    port_connections = []
    for signal, (sig_type, width) in signal_dict.items():
        # 只连接 input 和 output 信号
        if sig_type in (1, 3):
            port_connections.append("    .{}({})".format(signal, signal))
    tb_lines.append(",\n".join(port_connections))
    tb_lines.append("\n    );\n")
    
    # 使用解析出来的 clk 和 rst 信号名
    tb_lines.append("\n// 时钟激励\n")
    tb_lines.append("initial begin\n")
    tb_lines.append("    {} = 0;\n".format(clk_name))
    tb_lines.append("    forever #5 {} = ~{};\n".format(clk_name, clk_name))
    tb_lines.append("end\n")
    
    tb_lines.append("\n// 复位激励\n")
    tb_lines.append("initial begin\n")
    tb_lines.append("    {} = 1;\n".format(rst_name))
    tb_lines.append("    #10;\n")
    tb_lines.append("    {} = 0;\n".format(rst_name))
    tb_lines.append("end\n")
    
    # 将生成的内容写入文件
    full_path = os.path.join(fl_path, tb_filename)
    with open(full_path, "w", encoding='utf-8') as f:
        f.writelines(tb_lines)
    print("Testbench 文件已生成：", os.path.abspath(full_path))

    return 0

def main():
    # if len(sys.argv) < 2:
    #     print("Usage: python script.py <verilog_module_file>")
    #     sys.exit(1)
    
    # filename = sys.argv[1]


    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        sys.exit(1)
    
    inputs = parse_inputs(content)
    if not inputs:
        print("未能识别到任何输入信号。")
        sys.exit(1)

    generate_tb(signals_new, module_name)
    generate_random_stimulus(inputs, num_cycles)
    print("已完成testbench生成！\n")

if __name__ == '__main__':
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="Verilog Processor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 添加必须参数
    parser.add_argument("module", 
                      type=str,
                      help="Name of the target Verilog module")
    parser.add_argument("cycles", 
                      type=int,
                      help="Number of cycles to run the testbench")    
    
    # 可选参数示例
    parser.add_argument("-o", "--output",
                      default="_1",
                      help="Output file suffix")
    
    # 解析参数
    args = parser.parse_args()

    module_name = args.module

    num_cycles = args.cycles
    fl_path = f"d:/mylife_yanjiu/project/concolic_on_RTL/RTL/{module_name}/"
    filename = fl_path + f"{module_name}_1.v"
    signals_new = parse_verilog_new(filename)
    clk_name, rst_name = find_clk_rst(signals_new)
    main()
