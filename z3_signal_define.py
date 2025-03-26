# signal_inout = {'in': 8, 'clk': 1, 'rst': 1, 'out': 8, 'state': 4, 'st': 4, 'st2': 4}
signal_inout = {'clk':1, 'W_in':1, 'A_in':1, 'sensor':1, 'motor':1, 'next_state':2, 'state':2} 
import re
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

def get_z3_code(signal_inout):
    # 自动生成 Z3Py 定义的代码字符串
    z3_code = ""
    for signal_name, bit_width in signal_inout.items():
        z3_code += f"{signal_name} = BitVec('{signal_name}', {bit_width})\n"
    return z3_code

if __name__ == "__main__":
    # verilog_file = "d:/mylife_yanjiu/project/concolic_on_RTL/RTL/core/clint/clint.v"  # Verilog 源代码
    verilog_file = "d:/mylife_yanjiu/project/concolic_on_RTL/RTL/case3/case3_1.v"  # Verilog 源代码
    signals = parse_verilog_signals(verilog_file)
    print(signals)
    print("自动生成的 Z3Py 代码：\n")
    print(get_z3_code(signals))
