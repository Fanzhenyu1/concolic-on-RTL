import re
from z3 import *

def parse_add_sub(condition, in_comparison):
    """
    处理包含 '+' 或 '-' 的表达式，避免无限递归。
    按照从左到右的顺序进行解析，构造出正确的加/减运算表达式。
    """
    # 利用 re.split 分割出操作数和运算符，同时去除空项
    tokens = [t.strip() for t in re.split(r'([+-])', condition) if t.strip() != '']
    # 对每个 token，如果是运算符，则保留；否则递归解析
    parsed_tokens = []
    for token in tokens:
        if token in ['+', '-']:
            parsed_tokens.append(token)
        else:
            parsed_tokens.append(parse_condition(token, in_comparison))
    # 按照从左到右的顺序组合表达式
    if in_comparison:
        expr = parsed_tokens[0]
        i = 1
        while i < len(parsed_tokens):
            op = parsed_tokens[i]
            right = parsed_tokens[i+1]
            expr = f"({expr} {op} {right})"
            i += 2
        return expr
    else:
        expr = parsed_tokens[0]
        i = 1
        while i < len(parsed_tokens):
            op = parsed_tokens[i]
            right = parsed_tokens[i+1]
            if op == '+':
                expr = f"Plus({expr}, {right})"
            else:
                expr = f"Minus({expr}, {right})"
            i += 2
        return expr
    
def parse_verilog_const(const_str, in_comparison=False):
    """
    将 Verilog 常量转换为对应的表达式。
    对于带宽度信息的常量（例如 2'd1、4'b1010、8'hFF）：
      - 在比较上下文（in_comparison=True）下返回 BitVecVal 表达式，
      - 否则，对于1位常量返回布尔 True/False，其它情况返回 BitVecVal 表达式。
    """
    const_str = const_str.strip()
    # 匹配二进制常量，例如 8'b1010_1100 或 1'b1
    m = re.match(r"^(\d+)'[bB]([01_]+)$", const_str)
    if m:
        width, bits = m.groups()
        # 去掉下划线
        bitstr = bits.replace("_", "")
        val = int(bitstr, 2)
        if in_comparison:
            return f"BitVecVal({val}, {width})"
        else:
            if width == "1":
                return "True" if val == 1 else "False"
            else:
                return f"BitVecVal({val}, {width})"

    # 匹配十进制常量，例如 16'd123_456
    m = re.match(r"^(\d+)'[dD]([\d_]+)$", const_str)
    if m:
        width, number = m.groups()
        numstr = number.replace("_", "")
        val = int(numstr, 10)
        if in_comparison:
            return f"BitVecVal({val}, {width})"
        else:
            if width == "1":
                return "True" if val == 1 else "False"
            else:
                return f"BitVecVal({val}, {width})"
    # 匹配十六进制常量，例如 128'h00112233_44556677_8899aabb_ccddeeff
    m = re.match(r"^(\d+)'[hH]([0-9A-Fa-f_]+)$", const_str)
    if m:
        width, hex_num = m.groups()
        # 去掉所有下划线
        hex_digits = hex_num.replace("_", "")
        if in_comparison:
            return f"BitVecVal({int(hex_digits, 16)}, {width})"
        else:
            if width == "1":
                # 单比特时可以映射到布尔
                return "True" if int(hex_digits, 16) == 1 else "False"
            else:
                return f"BitVecVal({int(hex_digits, 16)}, {width})"
    # 纯数字（无宽度信息）的情况
    if const_str.isdigit():
        if in_comparison:
            return f"BitVecVal({const_str}, 1)"  # WIDTH根据实际情况设定
        else:
            return "True" if const_str != "0" else "False"
    return const_str

def split_top_level(s: str, delim: str):
    """
    只在 括号深度 == 0 时 按 delim 切分 s。
    如果能切出多于 1 段，就返回那几段，否则返回 None。
    支持 delim 是多字符的运算符（例如 '==', '!='）。
    """
    parts = []
    buf = []
    depth = 0
    i = 0
    L = len(s)
    D = len(delim)
    while i < L:
        c = s[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        # 只有在最外层才尝试匹配 delim
        if depth == 0 and s[i:i+D] == delim:
            parts.append(''.join(buf).strip())
            buf = []
            i += D
            continue
        buf.append(c)
        i += 1
    if buf:
        parts.append(''.join(buf).strip())
    return parts if len(parts) > 1 else None

def parse_condition(condition, in_comparison=False):
    """
    递归解析 Verilog 条件表达式，生成适用于所有信号为 BitVec 的 Z3 约束字符串。
    参数 in_comparison 用来指示当前解析是否处于比较上下文：
      - True：裸变量和运算保留为位向量形式（不转换为布尔），
      - False：裸变量转换为 (var != 0) 以得到布尔表达式。
    """
    condition = condition.strip()
    pass
    # 如果整个表达式被外层括号包裹，则剥除之
    if condition.startswith('(') and condition.endswith(')'):
        depth = 0
        remove = True
        for i, c in enumerate(condition):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0 and i < len(condition) - 1:
                    remove = False
                    break
        if remove:
            return parse_condition(condition[1:-1].strip(), in_comparison)

    # 处理比较运算符（==, !=, >, <, >=, <=）
    cmp_ops = [
        ('>=', '>='),
        ('<=', '<='),
        ('>',  '>'),
        ('<',  '<'),
        ('==', '=='),
        ('!=', '!=')
    ]
    for op_symbol, _ in cmp_ops:
        parts = split_top_level(condition, op_symbol)
        if parts is not None and len(parts) == 2:
            lhs, rhs = parts
            parsed_lhs = parse_condition(lhs.strip(), in_comparison=True)
            parsed_rhs = parse_condition(rhs.strip(), in_comparison=True)
            return f"({parsed_lhs} {op_symbol} {parsed_rhs})"

    # 先尝试顶层查找逻辑二元操作符（&&、||）
    for op in ['&&', '||']:
        parts = split_top_level(condition, op)
        if parts is not None:
            parsed_parts = [parse_condition(p, in_comparison=False) for p in parts]
            if op == '&&':
                return f"And({', '.join(parsed_parts)})"
            else:
                return f"Or({', '.join(parsed_parts)})"

    # 处理归约操作符，如 |(...) 或 &(...)
    if re.match(r'^[|&]\(.*\)$', condition):
        op = condition[0]
        m = re.search(r'\((.*)\)$', condition)
        if m:
            inner_expr = m.group(1).strip()
            parsed_inner = parse_condition(inner_expr, in_comparison=True)
            # if op == '|':
            #     return f"({parsed_inner} != BitVecVal(0, {parsed_inner}.size()))"
            # else:
            #     return f"({parsed_inner} == BitVecVal((1 << {parsed_inner}.size()) - 1, {parsed_inner}.size()))"
            
            if op == '|':
                return (f"If({parsed_inner} == BitVecVal(0, {parsed_inner}.size()), "
                    f"BitVecVal(0, 1), BitVecVal(1, 1))")
            else:
                return (f"If({parsed_inner} == BitVecVal((1 << {parsed_inner}.size()) - 1, {parsed_inner}.size()), "
                    f"BitVecVal(1, 1), BitVecVal(0, 1))")            

    # 再查找顶层的按位运算符（&、|）
    for op in ['&', '|']:
        parts = split_top_level(condition, op)
        if parts is not None:
            parsed_parts = [parse_condition(p.strip(), in_comparison) for p in parts]
            if in_comparison:
                # 在比较上下文中保持位向量运算
                join_op = f" {op} "
                return "(" + join_op.join(parsed_parts) + ")"
            else:
                # 否则转换为逻辑运算
                if op == '&':
                    return f"And({', '.join(parsed_parts)})"
                else:
                    return f"Or({', '.join(parsed_parts)})"
    

    
    # 处理逻辑非 ! 运算符
    if condition.startswith('!'):
        if in_comparison:
            # 对于位向量，在比较上下文中，!X 按 Verilog 语义返回 1'b1 当 X==0，否则返回 1'b0
            inner = parse_condition(condition[1:].strip(), in_comparison=True)
            # return f"If({inner} == 0, BitVecVal(1, 1), BitVecVal(0, 1))"
            return f"({inner} ^ BitVecVal(1,1))"  # 位异或实现取反
        else:
            inner = parse_condition(condition[1:].strip(), in_comparison=False)
            return f"Not({inner})"
    
    # 处理按位非 ~ 运算符（直接保留为位向量运算）
    if condition.startswith('~'):
        inner = parse_condition(condition[1:].strip(), in_comparison=True)
        return f"(~{inner})"
    
    # 处理 syms_dict["sig"][msb:lsb]
    m = re.match(r'^(syms_dict\["\w+"\])\[(\d+):(\d+)\]$', condition)
    if m:
        var_expr, msb, lsb = m.groups()
        return f"Extract({msb}, {lsb}, {var_expr})"
    # 处理位选择，例如 a[3:0]
    m = re.match(r'^(\w+)\[(\d+)(?::(\d+))?\]$', condition)
    if m:
        var, msb, lsb = m.groups()
        if lsb is None:
            return f"Extract({msb}, {msb}, {var})"
        else:
            return f"Extract({msb}, {lsb}, {var})"
    
    # 处理位拼接，例如 {a, b}
    # if condition.startswith('{'):
    #     m = re.findall(r'\{([^}]+)\}', condition)
    #     if m:
    #         parts = m[0].split(',')
    #         parsed_parts = [parse_condition(p.strip(), in_comparison=False) for p in parts]
    #         return f"Concat({', '.join(parsed_parts)})"
    if condition.startswith('{') and condition.endswith('}'):
        inner = condition[1:-1].strip()
        parts = split_top_level(inner, ',')
        # 对每一部分都保持位向量形式解析
        parsed_parts = [parse_condition(p.strip(), in_comparison=True) for p in parts]
        return f"Concat({', '.join(parsed_parts)})"
    
    # # 处理按位运算符 & 和 |（非 && 和 ||）
    # if '&' in condition and '&&' not in condition:
    #     parts = [p.strip() for p in condition.split('&')]
    #     parsed_parts = [parse_condition(p, in_comparison) for p in parts]
    #     if in_comparison:
    #         # 在比较上下文中保持位向量运算，直接用 & 连接
    #         return "(" + " & ".join(parsed_parts) + ")"
    #     else:
    #         # 否则转换为逻辑 And（布尔表达式）
    #         return f"And({', '.join(parsed_parts)})"
    # if '|' in condition and '||' not in condition:
    #     parts = [p.strip() for p in condition.split('|')]
    #     parsed_parts = [parse_condition(p, in_comparison) for p in parts]
    #     if in_comparison:
    #         return "(" + " | ".join(parsed_parts) + ")"
    #     else:
    #         return f"Or({', '.join(parsed_parts)})"
    
    # 先处理加法和减法，避免后续正则匹配遗漏
    if '+' in condition or '-' in condition:
        # 注意：只有当 '+' 或 '-' 是顶层运算符时才处理
        # 检查顶层（利用 split_top_level 也可以，但这里简单处理）
        # 若条件中含有加减运算符，则调用专用函数解析
        return parse_add_sub(condition, in_comparison)

    # 处理常量：纯数字或包含单引号的常量
    if re.match(r'^\d+$', condition) or ("'" in condition):
        return parse_verilog_const(condition, in_comparison)
    
    # 处理裸变量，例如 tagcomp_miss、state 等
    if (re.match(r'^[A-Za-z_]\w*$', condition) or re.match(r'^syms_dict\["[A-Za-z_]\w*"\]$', condition)):
        if in_comparison:
            return condition
        else:
            return f"({condition} != 0)"
    pass
    return condition

def is_boolean_expr(s: str) -> bool:
    """
    检测给定的 parse_condition() 输出字符串 s
    是否表示一个 BoolExpr（而不是纯 BitVecExpr）。
    规则：
      1) 剥外层括号
      2) 看最外层是否是 And(, Or(, Not(, If(
      3) 用 split_top_level 在深度0找比较运算符
    """
    t = s.strip()
    # 剥掉外层括号
    while t.startswith('(') and t.endswith(')'):
        # 确保括号匹配
        depth = 0
        for i,ch in enumerate(t):
            if ch=='(': depth+=1
            elif ch==')': depth-=1
            if depth==0 and i < len(t)-1:
                break
        else:
            t = t[1:-1].strip()
            continue
        break

    # 逻辑函数
    if any(t.startswith(pref) for pref in ('And(', 'Or(', 'Not(', 'If(')):
        return True

    # 顶层比较运算
    for op in ('==','!=','<=','>=','<','>'):
        if split_top_level(t, op):
            return True

    return False

# Parse Verilog action (e.g., "a <= 2'b0; b <= c? 2'b1 : d;")
def parse_action(assignment):
    """
    解析 Verilog 赋值语句（非阻塞和阻塞赋值），转换为 Z3 约束。
    示例输入:  'i_rx_phy_se0_s <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s));'
    示例输出:  'i_rx_phy_se0_s == And(Not(i_rx_phy_rxdp_s), Not(i_rx_phy_rxdn_s))'
    """
    assignment = assignment.strip().rstrip(';')  # 去除两端空格和末尾的 `;`
    
    # 使用正则匹配变量、赋值运算符（<= 或 =）和表达式
    match = re.match(r"(\w+)\s*(<=|=)\s*(.*)", assignment)
    if not match:
        raise ValueError("无效的 Verilog 赋值语句格式: " + assignment)
    
    lhs, op, rhs = match.groups()  # 提取左侧变量、赋值运算符和右侧表达式
    
    # 右侧表达式解析
    parsed_rhs = parse_condition(rhs, in_comparison=True)  # 解析右侧表达式
    
    # 2) 如果它是 BoolExpr，就 wrap 一下
    if is_boolean_expr(parsed_rhs):
        parsed_rhs = f"If({parsed_rhs}, BitVecVal(1,1), BitVecVal(0,1))"

    # 赋值转换为 Z3 等式约束
    return f"{lhs} == {parsed_rhs}"

# Main function to convert Verilog constraints to Z3 constraints
def verilog_to_z3(constraint_stack, signals_inout, signals_midle):      
#signals_inout, signals_midle are dictionaries of VerilogSignal objects
    z3_constraints = []
    list_signals_inconstraint = []
    pass
    while constraint_stack:
        pass
        constraint_pop = constraint_stack.pop()

        if (';' not in constraint_pop): # Determine condition statement
            # Parse condition
            condition_constraint = parse_condition(constraint_pop)
            z3_constraints.append(condition_constraint)
            # list_signals_inconstraint.extend(signal_list_condition)
        elif (';' in constraint_pop): # Determine action statement
            left_match = re.match(
                r"^\s*(\w+)\s*(?:$$.*?$$)?\s*(?:=|<=)\s*", 
                constraint_pop.split(';')[0]  # 移除可能干扰的结尾分号
            )
            if not left_match:
                return False
            left_signal = left_match.group(1)

            # 阶段2：精准分割右侧表达式（兼容所有赋值类型）
            if '<=' in constraint_pop:
                right_segment = constraint_pop.split('<=', 1)[-1].split(';')[0]
            else:
                right_segment = constraint_pop.split('=', 1)[-1].split(';')[0]

            # if left_signal in right_segment: # 需要完整匹配一个单词，而非简单的包含关系
            if re.search(r'\b{}\b'.format(re.escape(left_signal)), right_segment):
                z3_constraints = []
                return list_signals_inconstraint, z3_constraints
            else:
            # Parse action
                constraint_pop_list = constraint_pop.split(';')[:-1]
                for action_part in constraint_pop_list:
                    action_constraint = parse_action(action_part)
                    z3_constraints.append(action_constraint)
                    # list_signals_inconstraint.extend(signal_list_action)

    # delete duplicate signals
    # list_signals_inconstraint = list(set(list_signals_inconstraint))
    pass
    return list_signals_inconstraint, z3_constraints


def main_z3_solver(constraint_stack, signal_inout, signal_midle):
    # Create Verilog signal objects
    # signals_inout = {name: VerilogSignal(name, size) for name, size in signal_inout.items()}
    # signals_midle = {name: VerilogSignal(name, size) for name, size in signal_midle.items()}

    # Convert Verilog constraints to Z3 constraints
    # constraint_stack: list of constraints in Verilog format
    signal_list, constraints = verilog_to_z3(constraint_stack, signal_inout, signal_midle)

    # Create Z3 solver and add constraints
    pass
    solver = Solver()
    # solver.add(eval("'And((!ic_en), (hitmiss_eval & !icqmem_cycstb_i), (biudata_error), (cache_inhibit & biudata_valid))'"))
    # solver.add(Not(Or((ic_en == 0), (hitmiss_eval & (icqmem_cycstb_i == 0)) != 0, (biudata_error != 0), (cache_inhibit & biudata_valid) != 0)))
    for constraint in constraints:
        solver.add(eval(constraint))



    # Check if constraints are satisfiable
    if solver.check() == sat:
        model = solver.model()
        print("Constraints are satisfiable.")
        print(model)

        # value = [model[value[0]].as_long() for key,value in signal_inout.items()]
        # value_width = [value[1] for key,value in signal_inout.items()]
        # binary_representation = [bin(x)[2:].zfill(y) for x,y in zip(value,value_width)]
        # print(binary_representation)
        
    else:
        print("Constraints are unsatisfiable.")

###############################-----------------------------###############



# Example usage
# constraint_stack1 = ["r_in == 6'b101010", "a <= r_in;", "b < a & 6'b100100", "b <= 6'b100110"]
# constraint_stack2 = ["byte_controller_bit_controller_cmd_stop <= (byte_controller_core_cmd == 4'b0010);"]

# wb_clk_i = BitVec('wb_clk_i', 1)
# rst_i = BitVec('rst_i', 1)
# wb_adr_i = BitVec('wb_adr_i', 3)
# wb_dat_i = BitVec('wb_dat_i', 8)
# wb_dat_o = BitVec('wb_dat_o', 8)
# wb_we_i = BitVec('wb_we_i', 1)
# wb_stb_i = BitVec('wb_stb_i', 1)
# wb_cyc_i = BitVec('wb_cyc_i', 1)
# wb_ack_o = BitVec('wb_ack_o', 1)
# wb_inta_o = BitVec('wb_inta_o', 1)
# scl_pad_i = BitVec('scl_pad_i', 1)
# scl_pad_o = BitVec('scl_pad_o', 1)
# scl_padoen_o = BitVec('scl_padoen_o', 1)
# sda_pad_i = BitVec('sda_pad_i', 1)
# sda_pad_o = BitVec('sda_pad_o', 1)
# sda_padoen_o = BitVec('sda_padoen_o', 1)
# prer = BitVec('prer', 16)
# ctr = BitVec('ctr', 8)
# txr = BitVec('txr', 8)
# cr = BitVec('cr', 8)
# rxack = BitVec('rxack', 1)
# tip = BitVec('tip', 1)
# irq_flag = BitVec('irq_flag', 1)
# i2c_busy = BitVec('i2c_busy', 1)
# al = BitVec('al', 1)
# wb_wacc = BitVec('wb_wacc', 1)
# sta = BitVec('sta', 1)
# sto = BitVec('sto', 1)
# rd = BitVec('rd', 1)
# wr = BitVec('wr', 1)
# ack = BitVec('ack', 1)
# iack = BitVec('iack', 1)
# byte_controller_dout = BitVec('byte_controller_dout', 8)
# byte_controller_i2c_busy = BitVec('byte_controller_i2c_busy', 1)
# byte_controller_i2c_al = BitVec('byte_controller_i2c_al', 1)
# byte_controller_cmd_ack = BitVec('byte_controller_cmd_ack', 1)
# byte_controller_ack_out = BitVec('byte_controller_ack_out', 1)
# byte_controller_core_cmd = BitVec('byte_controller_core_cmd', 4)
# byte_controller_core_txd = BitVec('byte_controller_core_txd', 1)
# byte_controller_sr = BitVec('byte_controller_sr', 8)
# byte_controller_shift = BitVec('byte_controller_shift', 1)
# byte_controller_ld = BitVec('byte_controller_ld', 1)
# byte_controller_dcnt = BitVec('byte_controller_dcnt', 3)
# byte_controller_c_state = BitVec('byte_controller_c_state', 5)
# byte_controller_target = BitVec('byte_controller_target', 1)
# byte_controller_bit_controller_scl_o = BitVec('byte_controller_bit_controller_scl_o', 1)
# byte_controller_bit_controller_sda_o = BitVec('byte_controller_bit_controller_sda_o', 1)
# byte_controller_bit_controller_cmd_ack = BitVec('byte_controller_bit_controller_cmd_ack', 1)
# byte_controller_bit_controller_busy = BitVec('byte_controller_bit_controller_busy', 1)
# byte_controller_bit_controller_al = BitVec('byte_controller_bit_controller_al', 1)    
# byte_controller_bit_controller_dout = BitVec('byte_controller_bit_controller_dout', 1)
# byte_controller_bit_controller_scl_oen = BitVec('byte_controller_bit_controller_scl_oen', 1)
# byte_controller_bit_controller_sda_oen = BitVec('byte_controller_bit_controller_sda_oen', 1)
# byte_controller_bit_controller_sSCL = BitVec('byte_controller_bit_controller_sSCL', 1)
# byte_controller_bit_controller_sSDB = BitVec('byte_controller_bit_controller_sSDB', 1)
# byte_controller_bit_controller_dscl_oen = BitVec('byte_controller_bit_controller_dscl_oen', 1)
# byte_controller_bit_controller_sda_chk = BitVec('byte_controller_bit_controller_sda_chk', 1)
# byte_controller_bit_controller_clk_en = BitVec('byte_controller_bit_controller_clk_en', 1)
# byte_controller_bit_controller_cnt = BitVec('byte_controller_bit_controller_cnt', 16) 
# byte_controller_bit_controller_c_state = BitVec('byte_controller_bit_controller_c_state', 17)
# byte_controller_bit_controller_dSCL = BitVec('byte_controller_bit_controller_dSCL', 1)
# byte_controller_bit_controller_dSDA = BitVec('byte_controller_bit_controller_dSDA', 1)
# byte_controller_bit_controller_sta_condition = BitVec('byte_controller_bit_controller_sta_condition', 1)
# byte_controller_bit_controller_sto_condition = BitVec('byte_controller_bit_controller_sto_condition', 1)
# byte_controller_bit_controller_cmd_stop = BitVec('byte_controller_bit_controller_cmd_stop', 1)   


# main_z3_solver(constraint_stack2, {}, {})

# for i in range(len(constraint_stack_list)):
#     constraint_stack = constraint_stack_list[i]
#     solver = Solver()
#     main_z3_solver(constraint_stack, {}, {})
#     if solver.check() == sat:
#         print("Constraints are satisfiable.")
#     else:
#         target_path_C[i] = []
#         print("Constraints are unsatisfiable.")

# Create Z3 solver and add constraints
# main_z3_solver(constraint_stack1, signal_inout, {})
###############################-----------------------------###############