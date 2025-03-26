import re
import sys

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
    code_lines.append("integer i;")
    code_lines.append("initial begin")
    for signal, width in inputs:
        code_lines.append(f"    {signal} = 0;")
    code_lines.append("    #10;")
    code_lines.append(f"    for(i = 0; i < {num_cycles}; i = i + 1) begin")
    code_lines.append("        $display(\"********Period %d********\", i);")
    for signal, width in inputs:
        if width >= 32:
            # $random 返回32位数
            code_lines.append(f"        {signal} = $random;")
        else:
            mask = (1 << width) - 1
            code_lines.append(f"        {signal} = $random & {width}'d{mask};")
    code_lines.append("        #10;")
    code_lines.append("    end")
    code_lines.append("    $finish;")
    code_lines.append("end")
    code_lines.append("initial begin")
    code_lines.append("    $dumpfile(\"wave.vcd\");")
    code_lines.append("    $dumpvars(0, tb_***);")
    code_lines.append("end")
    return "\n".join(code_lines)

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
    
    stimulus = generate_random_stimulus(inputs)
    print("生成的随机化输入测试代码如下：\n")
    print(stimulus)

if __name__ == '__main__':
    fl_path = "d:/mylife_yanjiu/project/concolic_on_RTL/RTL/usb_phy/"
    filename = fl_path + "usb_phy_1.v"
    main()
