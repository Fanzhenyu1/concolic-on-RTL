import re

def parse_defines(define_file):
    """ 解析 Verilog `define` 宏定义 """
    defines = {}
    with open(define_file, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.match(r'`define\s+(\w+)\s+(.+)', line.strip())
            if match:
                macro_name, macro_value = match.groups()
                defines[macro_name] = macro_value.strip()
    return defines

def replace_macros(verilog_file, defines, output_file):
    """ 在 Verilog 文件中替换 `define` 宏 """
    with open(verilog_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    for macro, value in defines.items():
        content = re.sub(rf'`{macro}\b', value, content)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"替换完成，生成文件：{output_file}")

if __name__ == "__main__":
    define_file = "d:/mylife_yanjiu/project/concolic_on_RTL/RTL/core/defines.v"  # 宏定义文件
    verilog_file = "d:/mylife_yanjiu/project/concolic_on_RTL/RTL/core/csr_reg/csr_reg.v"  # Verilog 源代码
    output_file = "d:/mylife_yanjiu/project/concolic_on_RTL/RTL/core/csr_reg/csr_reg_1.v"  # 处理后的输出文件
    
    defines = parse_defines(define_file)
    replace_macros(verilog_file, defines, output_file)
