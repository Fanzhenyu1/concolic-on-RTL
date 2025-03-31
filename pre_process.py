import re
import argparse

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

def replace_verilog_parameters(input_file, output_file):
    # 匹配Verilog参数定义的正则表达式
    param_pattern = re.compile(r'^\s*parameter\s+(\w+)\s*=\s*([^;]+);')

    # 读取文件内容并提取参数
    with open(input_file, 'r') as f:
        lines = f.readlines()

    params = {}
    clean_lines = []
    
    # 第一次遍历：提取参数并清理参数行
    for line in lines:
        match = param_pattern.match(line)
        if match:
            param_name = match.group(1)
            param_value = match.group(2).strip()
            params[param_name] = param_value
        else:
            clean_lines.append(line)

    # 第二次遍历：替换参数引用
    processed_lines = []
    for line in clean_lines:
        # 按名称长度降序排列，避免短名称误匹配
        for name in sorted(params, key=lambda x: len(x), reverse=True):
            pattern = r'\b' + re.escape(name) + r'\b'
            line = re.sub(pattern, params[name], line)
        processed_lines.append(line)

    # 写入输出文件
    with open(output_file, 'w') as f:
        f.writelines(processed_lines)

def add_wire_reg_declarations(content):
    lines = content.split('\n')
    input_lines = []  # 保存input声明行的索引和信号信息
    output_signals = []  # 保存output信号的信息：name, line_num, has_reg, has_wire, line

    # 第一步：收集input和output信号的信息
    for line_num, line in enumerate(lines):
        # 匹配input声明（处理单行多信号）
        if re.match(r'^\s*input\b', line):
            has_wire_reg = re.search(r'\b(wire|reg)\b', line) is not None
            signals = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b(?=\s*[,;])', line)
            for _ in signals:
                input_lines.append( (line_num, line, has_wire_reg) )
        
        # 匹配output声明（处理多信号）
        if re.match(r'^\s*output\b', line):
            has_reg = re.search(r'\breg\b', line) is not None
            has_wire = re.search(r'\bwire\b', line) is not None
            signals = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b(?=\s*[,;])', line)
            for sig_name in signals:
                output_signals.append({
                    'name': sig_name,
                    'line_num': line_num,
                    'has_reg': has_reg,
                    'has_wire': has_wire,
                    'line': line
                })

    # 第二步：检查每个output信号是否被过程赋值或连续赋值
    content_str = '\n'.join(lines)
    for sig in output_signals:
        # 跳过已有明确类型声明的信号
        if sig['has_reg'] or sig['has_wire']:
            continue
        
        signal_name = re.escape(sig['name'])
        line_num = sig['line_num']
        old_line = lines[line_num]

        # 检测在always/initial块中的非阻塞或阻塞赋值
        always_pattern = (
            r'\b(always|initial)\b.*?'          # 匹配过程块开始
            r'%s\s*([<=]=)\s*[^=]' % signal_name # 匹配信号后接<=或=（排除==）
        )
        in_always = re.search(always_pattern, content_str, re.DOTALL | re.IGNORECASE)

        # 检测在assign语句中的阻塞赋值
        assign_pattern = (
            r'\bassign\b\s*'    # 匹配assign关键字
            r'(?:[\w$.]+\s*\.\s*)*%s\s*=' % signal_name # 匹配层次化信号
        )
        in_assign = re.search(assign_pattern, content_str, re.IGNORECASE)

        # 根据检测结果修改声明
        if in_always:
            # 替换为output reg（保留原格式）
            new_line = re.sub(r'(\boutput\b)(\s+)(?!reg\b)', r'\1 reg\2', old_line)
            lines[line_num] = new_line
        elif in_assign and not sig['has_reg']:
            # 替换为output wire（保留原格式）
            new_line = re.sub(r'(\boutput\b)(\s+)(?!wire\b)', r'\1 wire\2', old_line)
            lines[line_num] = new_line

    # 第三步：处理input行，添加wire（如果没有wire/reg）
    for line_num, old_line, has_wire_reg in input_lines:
        if not has_wire_reg:
            new_line = re.sub(
                r'(\binput\b)(\s+)(?!wire\b)(?!reg\b)',
                r'\1 wire\2',
                old_line
            )
            lines[line_num] = new_line

    return '\n'.join(lines)

def process_verilog_file(file_path):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 处理内容
    modified_content = add_wire_reg_declarations(content)
    
    # 写回原文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)

def main(module_name):
    # define_file = "d:/mylife_yanjiu/project/concolic_on_RTL/RTL/or1200_ICache/src/or1200_defines.v"  # 宏定义文件
    verilog_file = f"d:/mylife_yanjiu/project/concolic_on_RTL/RTL/{module_name}/src/{module_name}.v"  # Verilog 源代码
    output_file = f"d:/mylife_yanjiu/project/concolic_on_RTL/RTL/{module_name}/{module_name}_1.v"  # 处理后的输出文件
    # defines = parse_defines(define_file)
    # replace_macros(verilog_file, defines, output_file)    
    replace_verilog_parameters(verilog_file, output_file)
    process_verilog_file(output_file)


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