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
    # 匹配二进制常量，例如 1'b1 或 1'b0
    m = re.match(r"^(\d+)'[bB]([01]+)$", const_str)
    if m:
        width, bits = m.groups()
        if in_comparison:
            return f"BitVecVal({int(bits, 2)}, {width})"
        else:
            if width == "1":
                return "True" if bits == "1" else "False"
            else:
                return f"BitVecVal({int(bits, 2)}, {width})"
    # 匹配十进制常量，例如 2'd3
    m = re.match(r"^(\d+)'[dD](\d+)$", const_str)
    if m:
        width, number = m.groups()
        if in_comparison:
            return f"BitVecVal({number}, {width})"
        else:
            if width == "1":
                return "True" if number == "1" else "False"
            else:
                return f"BitVecVal({number}, {width})"
    # 匹配十六进制常量，例如 8'hFF
    m = re.match(r"^(\d+)'[hH]([0-9a-fA-F]+)$", const_str)
    if m:
        width, hex_num = m.groups()
        if in_comparison:
            return f"BitVecVal({int(hex_num, 16)}, {width})"
        else:
            if width == "1":
                return "True" if int(hex_num, 16) == 1 else "False"
            else:
                return f"BitVecVal({int(hex_num, 16)}, {width})"
    # 纯数字（无宽度信息）的情况
    if const_str.isdigit():
        if in_comparison:
            return f"BitVecVal({const_str}, WIDTH)"  # WIDTH根据实际情况设定
        else:
            return "True" if const_str != "0" else "False"
    return const_str

def split_top_level(condition, op):
    """
    按 op 分割 condition，但只在顶层（括号深度为 0）分割。
    如果能分割则返回子表达式列表，否则返回 None。
    """
    parts = []
    depth = 0
    last_index = 0
    i = 0
    op_len = len(op)
    found = False
    while i < len(condition):
        c = condition[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        # 仅在深度为0时查找 op
        if depth == 0 and condition[i:i+op_len] == op:
            parts.append(condition[last_index:i].strip())
            last_index = i + op_len
            i += op_len
            found = True
            continue
        i += 1
    if found:
        parts.append(condition[last_index:].strip())
        return parts
    return None

def parse_condition(condition, in_comparison=False):
    """
    递归解析 Verilog 条件表达式，生成适用于所有信号为 BitVec 的 Z3 约束字符串。
    参数 in_comparison 用来指示当前解析是否处于比较上下文：
      - True：裸变量和运算保留为位向量形式（不转换为布尔），
      - False：裸变量转换为 (var != 0) 以得到布尔表达式。
    """
    condition = condition.strip()

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
    
    # 先尝试顶层查找逻辑二元操作符（&&、||）
    for op in ['&&', '||']:
        parts = split_top_level(condition, op)
        if parts is not None:
            parsed_parts = [parse_condition(p, in_comparison=False) for p in parts]
            if op == '&&':
                return f"And({', '.join(parsed_parts)})"
            else:
                return f"Or({', '.join(parsed_parts)})"
            
    # 再查找顶层的按位运算符（&、|）
    for op in ['&', '|']:
        parts = split_top_level(condition, op)
        if parts is not None:
            parsed_parts = [parse_condition(p, in_comparison) for p in parts]
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
    
    # 处理逻辑非 ! 运算符
    if condition.startswith('!'):
        if in_comparison:
            # 对于位向量，在比较上下文中，!X 按 Verilog 语义返回 1'b1 当 X==0，否则返回 1'b0
            inner = parse_condition(condition[1:].strip(), in_comparison=True)
            return f"If({inner} == 0, BitVecVal(1, 1), BitVecVal(0, 1))"
        else:
            inner = parse_condition(condition[1:].strip(), in_comparison=False)
            return f"Not({inner})"
    
    # 处理按位非 ~ 运算符（直接保留为位向量运算）
    if condition.startswith('~'):
        inner = parse_condition(condition[1:].strip(), in_comparison=True)
        return f"(~{inner})"
    
    # 处理归约操作符，如 |(...) 或 &(...)
    if re.match(r'^[|&]\(.*\)$', condition):
        op = condition[0]
        m = re.search(r'\((.*)\)$', condition)
        if m:
            inner = parse_condition(m.group(1).strip(), in_comparison=False)
            if op == '|':
                return f"({inner} != 0)"
            else:
                return f"({inner} == BitVecVal((1 << {inner}.size()) - 1, {inner}.size()))"
    
    # 处理位选择，例如 a[3:0]
    m = re.match(r'^(\w+)\[(\d+)(?::(\d+))?\]$', condition)
    if m:
        var, msb, lsb = m.groups()
        if lsb is None:
            return f"Extract({msb}, {msb}, {var})"
        else:
            return f"Extract({msb}, {lsb}, {var})"
    
    # 处理位拼接，例如 {a, b}
    if condition.startswith('{'):
        m = re.findall(r'\{([^}]+)\}', condition)
        if m:
            parts = m[0].split(',')
            parsed_parts = [parse_condition(p.strip(), in_comparison=False) for p in parts]
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
    if re.match(r'^[A-Za-z_]\w*$', condition):
        if in_comparison:
            return condition
        else:
            return f"({condition} != 0)"
    
    return condition


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
constraint_stack2 = ["(st2 == 4'h5)", 'st2 = st;', "st = state + 4'h2;", "state <= 4'h0;"]


# rst = BitVec('rst', 1)
# phy_tx_mode = BitVec('phy_tx_mode', 1)
# usb_rst = BitVec('usb_rst', 1)
# txdp = BitVec('txdp', 1)
# txdn = BitVec('txdn', 1)
# txoe = BitVec('txoe', 1)
# rxd = BitVec('rxd', 1)
# rxdp = BitVec('rxdp', 1)
# rxdn = BitVec('rxdn', 1)
# DataOut_i = BitVec('DataOut_i', 8)
# TxValid_i = BitVec('TxValid_i', 1)
# TxReady_o = BitVec('TxReady_o', 1)
# RxValid_o = BitVec('RxValid_o', 1)
# RxActive_o = BitVec('RxActive_o', 1)
# RxError_o = BitVec('RxError_o', 1)
# DataIn_o = BitVec('DataIn_o', 8)
# LineState_o = BitVec('LineState_o', 2)
# rst_cnt = BitVec('rst_cnt', 5)
# i_tx_phy_TxReady_o = BitVec('i_tx_phy_TxReady_o', 1)
# i_tx_phy_state = BitVec('i_tx_phy_state', 3)
# i_tx_phy_next_state = BitVec('i_tx_phy_next_state', 3)
# i_tx_phy_tx_ready_d = BitVec('i_tx_phy_tx_ready_d', 1)
# i_tx_phy_ld_sop_d = BitVec('i_tx_phy_ld_sop_d', 1)
# i_tx_phy_ld_data_d = BitVec('i_tx_phy_ld_data_d', 1)
# i_tx_phy_ld_eop_d = BitVec('i_tx_phy_ld_eop_d', 1)
# i_tx_phy_tx_ip = BitVec('i_tx_phy_tx_ip', 1)
# i_tx_phy_tx_ip_sync = BitVec('i_tx_phy_tx_ip_sync', 1)
# i_tx_phy_bit_cnt = BitVec('i_tx_phy_bit_cnt', 3)
# i_tx_phy_hold_reg = BitVec('i_tx_phy_hold_reg', 8)
# i_tx_phy_hold_reg_d = BitVec('i_tx_phy_hold_reg_d', 8)
# i_tx_phy_sd_raw_o = BitVec('i_tx_phy_sd_raw_o', 1)
# i_tx_phy_data_done = BitVec('i_tx_phy_data_done', 1)
# i_tx_phy_sft_done = BitVec('i_tx_phy_sft_done', 1)
# i_tx_phy_sft_done_r = BitVec('i_tx_phy_sft_done_r', 1)
# i_tx_phy_ld_data = BitVec('i_tx_phy_ld_data', 1)
# i_tx_phy_one_cnt = BitVec('i_tx_phy_one_cnt', 3)
# i_tx_phy_stuff = BitVec('i_tx_phy_stuff', 1)
# i_tx_phy_sd_bs_o = BitVec('i_tx_phy_sd_bs_o', 1)
# i_tx_phy_sd_nrzi_o = BitVec('i_tx_phy_sd_nrzi_o', 1)
# i_tx_phy_append_eop = BitVec('i_tx_phy_append_eop', 1)
# i_tx_phy_append_eop_sync1 = BitVec('i_tx_phy_append_eop_sync1', 1)
# i_tx_phy_append_eop_sync2 = BitVec('i_tx_phy_append_eop_sync2', 1)
# i_tx_phy_append_eop_sync3 = BitVec('i_tx_phy_append_eop_sync3', 1)
# i_tx_phy_append_eop_sync4 = BitVec('i_tx_phy_append_eop_sync4', 1)
# i_tx_phy_txdp = BitVec('i_tx_phy_txdp', 1)
# i_tx_phy_txdn = BitVec('i_tx_phy_txdn', 1)
# i_tx_phy_txoe_r1 = BitVec('i_tx_phy_txoe_r1', 1)
# i_tx_phy_txoe_r2 = BitVec('i_tx_phy_txoe_r2', 1)
# i_tx_phy_txoe = BitVec('i_tx_phy_txoe', 1)
# i_rx_phy_rxd_s0 = BitVec('i_rx_phy_rxd_s0', 1)
# i_rx_phy_rxd_s1 = BitVec('i_rx_phy_rxd_s1', 1)
# i_rx_phy_rxd_s = BitVec('i_rx_phy_rxd_s', 1)
# i_rx_phy_rxdp_s0 = BitVec('i_rx_phy_rxdp_s0', 1)
# i_rx_phy_rxdp_s1 = BitVec('i_rx_phy_rxdp_s1', 1)
# i_rx_phy_rxdp_s = BitVec('i_rx_phy_rxdp_s', 1)
# i_rx_phy_rxdp_s_r = BitVec('i_rx_phy_rxdp_s_r', 1)
# i_rx_phy_rxdn_s0 = BitVec('i_rx_phy_rxdn_s0', 1)
# i_rx_phy_rxdn_s1 = BitVec('i_rx_phy_rxdn_s1', 1)
# i_rx_phy_rxdn_s = BitVec('i_rx_phy_rxdn_s', 1)
# i_rx_phy_rxdn_s_r = BitVec('i_rx_phy_rxdn_s_r', 1)
# i_rx_phy_synced_d = BitVec('i_rx_phy_synced_d', 1)
# i_rx_phy_rxd_r = BitVec('i_rx_phy_rxd_r', 1)
# i_rx_phy_rx_en = BitVec('i_rx_phy_rx_en', 1)
# i_rx_phy_rx_active = BitVec('i_rx_phy_rx_active', 1)
# i_rx_phy_bit_cnt = BitVec('i_rx_phy_bit_cnt', 3)
# i_rx_phy_rx_valid1 = BitVec('i_rx_phy_rx_valid1', 1)
# i_rx_phy_rx_valid = BitVec('i_rx_phy_rx_valid', 1)
# i_rx_phy_shift_en = BitVec('i_rx_phy_shift_en', 1)
# i_rx_phy_sd_r = BitVec('i_rx_phy_sd_r', 1)
# i_rx_phy_sd_nrzi = BitVec('i_rx_phy_sd_nrzi', 1)
# i_rx_phy_hold_reg = BitVec('i_rx_phy_hold_reg', 8)
# i_rx_phy_one_cnt = BitVec('i_rx_phy_one_cnt', 3)
# i_rx_phy_dpll_state = BitVec('i_rx_phy_dpll_state', 2)
# i_rx_phy_dpll_next_state = BitVec('i_rx_phy_dpll_next_state', 2)
# i_rx_phy_fs_ce_d = BitVec('i_rx_phy_fs_ce_d', 1)
# i_rx_phy_fs_ce = BitVec('i_rx_phy_fs_ce', 1)
# i_rx_phy_fs_state = BitVec('i_rx_phy_fs_state', 3)
# i_rx_phy_fs_next_state = BitVec('i_rx_phy_fs_next_state', 3)
# i_rx_phy_rx_valid_r = BitVec('i_rx_phy_rx_valid_r', 1)
# i_rx_phy_sync_err_d = BitVec('i_rx_phy_sync_err_d', 1)
# i_rx_phy_sync_err = BitVec('i_rx_phy_sync_err', 1)
# i_rx_phy_bit_stuff_err = BitVec('i_rx_phy_bit_stuff_err', 1)
# i_rx_phy_se0_r = BitVec('i_rx_phy_se0_r', 1)
# i_rx_phy_byte_err = BitVec('i_rx_phy_byte_err', 1)
# i_rx_phy_se0_s = BitVec('i_rx_phy_se0_s', 1)
# i_rx_phy_fs_ce_r1 = BitVec('i_rx_phy_fs_ce_r1', 1)
# i_rx_phy_fs_ce_r2 = BitVec('i_rx_phy_fs_ce_r2', 1)

in_1 = BitVec('in_1', 8)
out = BitVec('out', 8)
clk = BitVec('clk', 1)
state = BitVec('state', 4)
st = BitVec('st', 4)
st2 = BitVec('st2', 4)

main_z3_solver(constraint_stack2, {}, {})

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