# signal_inout = {'clk':1, 'W_in':1, 'A_in':1, 'sensor':1, 'motor':1, 'next_state':2, 'state':2} 
import re
import argparse
def parse_verilog_signals(verilog_file):
    """ 解析 Verilog 信号定义，并转换为 Python 字典 """
    signal_inout = {}
    
    # 定义匹配信号的正则表达式
    signal_pattern = re.compile(r'\b(reg|wire)\s*(?:\[(\d+):\d+\])?\s*(\w+)')
    
    # 此处修改Verilog文件的编码格式，一般推荐使用utf-8
    # with open(verilog_file, 'r', encoding='utf-8') as file:
    with open(verilog_file, 'r', encoding='gb2312') as file:
        for line in file:
            match = signal_pattern.findall(line.strip())
            for signal_type, width, name in match:
                bit_width = int(width) + 1 if width else 1  # 默认位宽为 1
                signal_inout[name] = bit_width
    
    return signal_inout

def parse_verilog_new(verilog_file):
    """解析Verilog信号定义，生成包含信号类型和位宽的字典"""
    signal_def = {}
    port_signals = set()

    # 修正正则表达式
    direction_pattern = re.compile(
        r'^\s*(input|output|inout)\s*'        # 方向
        r'(?:wire|reg)?\s*'                   # 可选的 wire/reg
        r'(\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*'  # 可选的位宽定义
        r'([\w,\s]+?)\s*(?=[,;)])',           # 信号名，后面紧跟 , 或 ; 或 )
        re.MULTILINE
    )

    internal_pattern = re.compile(
        r'^\s*(reg|wire)\s*'                  # 类型（reg 或 wire）
        r'(\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*'  # 可选的位宽定义
        r'([\w,\s]+)\s*;',                    # 信号名
        re.MULTILINE
    )

    # 读取文件内容并预处理
    with open(verilog_file, 'r', encoding='gb2312') as file:
        content = file.read()

    # 移除单行注释
    content = re.sub(r'//.*', '', content)

    # 解析端口信号（input/output/inout）
    for match in direction_pattern.finditer(content):
        direction, width_full, width_high, width_low, signals_str = match.groups()
        width_high = int(width_high) if width_high else 0
        width_low = int(width_low) if width_low else 0
        bit_width = abs(width_high - width_low) + 1  # 计算位宽
        signals = [s.strip() for s in signals_str.split(',')]

        for signal in signals:
            if signal:
                code = 1 if direction == "input" else 3  # input: 1, output: 3
                signal_def[signal] = (code, bit_width)
                port_signals.add(signal)

    # 解析内部信号（reg/wire）
    for match in internal_pattern.finditer(content):
        sig_type, width_full, width_high, width_low, signals_str = match.groups()
        width_high = int(width_high) if width_high else 0
        width_low = int(width_low) if width_low else 0
        bit_width = abs(width_high - width_low) + 1  # 计算位宽
        signals = [s.strip() for s in signals_str.split(',')]

        for signal in signals:
            if signal and signal not in port_signals:
                signal_def[signal] = (2, bit_width)  # reg/wire 统一标记为 2

    return signal_def

def get_z3_code(signal_inout):
    # 自动生成 Z3Py 定义的代码字符串
    z3_code = ""
    for signal_name, bit_width in signal_inout.items():
        z3_code += f"    {signal_name} = BitVec('{signal_name}', {bit_width})\n"
    return z3_code

def main(module_name):
    verilog_file = f"d:/mylife_yanjiu/project/concolic_on_RTL/RTL/{module_name}/{module_name}_1.v"  # Verilog 源代码
    signals = parse_verilog_signals(verilog_file)
    print(signals)
    print("自动生成的 Z3Py 代码：\n")
    print(get_z3_code(signals))

    # 新版解析Verilog信号定义
    signals_new = parse_verilog_new(verilog_file)
    print(signals_new)

if __name__ == "__main__":
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="Verilog Processor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 添加必须参数
    parser.add_argument("module", 
                      type=str,
                      help="Name of the target Verilog module")
    
    # 可选参数示例
    parser.add_argument("-o", "--output",
                      default="_1",
                      help="Output file suffix")
    
    # 解析参数
    args = parser.parse_args()
    
    # 调用主函数
    main(module_name=args.module)
