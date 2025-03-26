import re
import os


def parse_conditions(verilog_code):
    """解析always块中的条件路径"""
    condition_pattern = r'else if\s*\((.*?)\)|if\s*\((.*?)\)'
    conditions = re.findall(condition_pattern, verilog_code, re.DOTALL)

    # 清理匹配结果
    clean_conds = []
    for pair in conditions:
        cond = pair[0] or pair[1]
        clean_conds.append(cond.replace('\n', ' ').strip())
    return clean_conds


def generate_advanced_tb(condition, vector):
    tb = "initial begin\n"
    tb += "  // 自动生成的测试序列\n"
    tb += f"  // 测试条件: {condition[0]}\n\n"

    # 遍历所有路径
    for path_name, path_vectors in vector.items():
        tb += f"  // {path_name} 测试向量\n"

        for idx, vec in enumerate(path_vectors, 1):
            tb += f"  // 测试用例 {idx}\n"
            tb += f"  reset = {1 if vec['reset'] else 0};\n"
            tb += f"  en = {1 if vec['en'] else 0};\n"
            tb += f"  a = 2'b{vec['a']:02b};\n"
            tb += f"  b = 2'b{vec['b']:02b};\n"
            tb += "  #10;\n\n"  # 添加延迟

    tb += "end\n"
    return tb


def generate_intelligent_tb(verilog_path):
    with open(verilog_path, 'r') as f:
        content = f.read()

    # 提取模块信息
    module_match = re.search(r'module\s+(\w+)\s*\(', content)
    module_name = module_match.group(1)

    # 提取端口信号
    ports = re.findall(r'(input|output)\s+(reg|wire)?\s*(\[.*?\])?\s*(\w+)', content)
    inputs = [p[3] for p in ports if p[0] == 'input']
    outputs = [p[3] for p in ports if p[0] == 'output']

    # 解析条件路径
    conditions = parse_conditions(content)
    tb_conditions = [
        "reset == 1'b1",
        "a == 2'b01",
        "(a == 2'b10) && (c == 2'b01)",
        "default case"
    ]
    test_vector = {
        "path1": [
            {
                "reset": True,  # 布尔值
                "en": False,  # 布尔值（可能为None表示无关项）
                "a": 0,  # 整型（0-3对应2位二进制）
                "b": 3  # 整型（0-3对应2位二进制）
            },
            # 更多向量...
        ],
        "path2": [
            {
                "reset": False,
                "en": True,
                "a": 1,  # 0x1 → 2'b01
                "b": 3
            }
        ],
        "path3": [
            {
                "reset": False,
                "en": True,
                "a": 2,  # 0x2 → 2'b10
                "b": 1  # 0x1 → 2'b01 → c=2'b01
            }
        ],
        "path4": [
            {
                "reset": False,
                "en": False,
                "a": 3,  # 0x3 → 2'b11
                "b": 0
            }
        ]
    }

    # 生成智能Testbench
    tb = f"`timescale 1ns/1ps\n\nmodule {module_name}_tb;\n"

    # 声明信号
    for port in ports:
        direction = port[0]
        sig_type = port[1] if port[1] else 'wire'
        size = port[2] if port[2] else ''
        name = port[3]
        tb += f"  reg {size} {name};\n" if direction == 'input' else f"  wire {size} {name};\n"

    # 添加时钟和复位参数
    tb += "\n  // 时钟和复位参数\n"
    tb += "  parameter CLK_PERIOD = 10;\n"
    tb += "  parameter RESET_CYCLES = 3;\n"

    # 实例化被测模块
    tb += f"\n  // 实例化被测模块\n  {module_name} uut (\n"
    tb += ',\n'.join([f"    .{port[3]}({port[3]})" for port in ports])
    tb += "\n  );\n\n"

    # 生成时钟
    tb += "  // 生成时钟\n"
    tb += "  initial begin\n"
    tb += "    forever #(CLK_PERIOD/2) clk = ~clk;\n"
    tb += "  end\n\n"

    # 生成复位和测试逻辑
    tb += "  // 测试逻辑\n"
    tb += "  initial begin\n"
    tb += "    // 初始化信号\n"
    tb += "    clk = 0;\n"
    tb += "    reset = 1;\n\n"

    tb += "    // 复位操作\n"
    tb += "    #RESET_CYCLES reset = 0;\n\n"

    tb += "    // 添加测试激励\n"
    tb += generate_advanced_tb(conditions, test_vector)

    tb += "    // 仿真控制\n"
    tb += "    #100 $finish;\n"
    tb += "  end\n\n"

    tb += "  // 波形记录\n"
    tb += "  initial begin\n"
    tb += "    $dumpfile(\"waveform.vcd\");\n"
    tb += "    $dumpvars(0, {module_name}_tb);\n"
    tb += "  end\n\n"

    tb += "endmodule"

    # 保存文件
    output_path = os.path.splitext(verilog_path)[0] + "_smart_tb.v"
    with open(output_path, 'w') as f:
        f.write(tb)

    return output_path


# 使用示例
if __name__ == "__main__":
    verilog_file = "D:/PycharmProj/test generation/simple_module/rtl/simple_module.v"
    tb_file = generate_intelligent_tb(verilog_file)
    print(f"智能Testbench已生成: {tb_file}")