from z3 import *
import re
import random
##input: verilog path constraint stack, signal list [a,b] || condition, such as "a==b", action, such as "a <= 2'b0;"
##output: Z3 solver constraint
# import path_reduction


# target_path_C, constraint_stack_list = path_reduction.main()
# Verilog signal class for easy management
# class VerilogSignal:
#     def __init__(self, name, size):
#         self.name = name
#         self.size = size
#         # self.var = BitVec(self.name, self.size)
#         pass
#     def Define_Vec(self):
#         self.var = BitVec(self.name, self.size)

# Parse Verilog condition (e.g., "a == b", "a <= b", "!(a == b)", "(a == 2'b0)&&(b > c)")
def parse_condition(condition):
    # initial output
    condition = condition.strip()                   # 去除两端空格
    condition_constraint = ""
    signal_list_condition = []
    signal_pattern = r'(?<!\')\b[a-zA-Z_]\w*\b'             # 匹配信号，但排除以单引号开头的数字常量
    constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量
    signals_in_condition = re.findall(signal_pattern, condition)
    constants_list = re.findall(constant_pattern, condition)
    signal_list_condition = signals_in_condition
    pass
    # Create Z3 constraints for condition

    
    if condition.startswith('!') or condition.startswith('~'):
        condition_new = condition[1:]
        pass
        return f"Not({parse_condition(condition_new)})"
    elif not any(op in condition for op in ('==', '!=', '>', '<', '>=', '<=', '&&', '||', "'", '|(', '&(')):
        return f"{condition}"
    elif condition.startswith('(') and condition.endswith(')'):
        # condition = condition[1:-1].strip()
        condition = condition.replace('(',' ').replace(')',' ').strip()
        pass
        return parse_condition(condition)
    
    # 处理归约或 |(signal)
    elif re.match(r'^\|\(', condition):
        inner_expr = re.sub(r'^\|\((.*)$\)?$', r'\1', condition)  # 支持多层括号
        inner_expr = inner_expr.strip().rstrip(')').strip()
        inner_z3 = parse_condition(inner_expr)
        pass
        return f"{inner_z3} != 0"
    
    # 处理归约与 &(signal)
    elif re.match(r'^\&\(', condition):
        inner_expr = re.sub(r'^&\((.*)$\)?$', r'\1', condition)
        inner_z3 = parse_condition(inner_expr)
        return f"And([Extract(i,i,{inner_z3}) for i in range({inner_z3}.size())])"

    elif '||' in condition:
        or_parts = condition.split("||")
        if len(or_parts) > 1:
            return f"Or({', '.join(parse_condition(part) for part in or_parts)})"
    elif '&&' in condition:  
        and_parts = condition.split("&&")
        for i in range(len(and_parts)):
            and_parts[i] = and_parts[i].strip()
            if re.match(r'^[a-zA-Z_]\w*$', and_parts[i]):
                and_parts[i] = f"{and_parts[i]} == 1'b1"
        pass
        if len(and_parts) > 1:
            pass
            return f"And({', '.join(parse_condition(part) for part in and_parts)})"
    elif '>' in condition or '>=' in condition:
        if '>=' in condition:
            uge_parts = condition.split(">=")
            if len(uge_parts) > 1:
                return f"UGE({', '.join(parse_condition(part) for part in uge_parts)})"
        elif '>' in condition:
            ugt_parts = condition.split(">")
            if len(ugt_parts) > 1:
                return f"UGT({', '.join(parse_condition(part) for part in ugt_parts)})"
    elif '<' in condition or '<=' in condition:
        if '<=' in condition:
            ule_parts = condition.split("<=")
            if len(ule_parts) > 1:
                return f"ULE({', '.join(parse_condition(part) for part in ule_parts)})"
        elif '<' in condition:
            ult_parts = condition.split("<")
            if len(ult_parts) > 1:
                return f"ULT({', '.join(parse_condition(part) for part in ult_parts)})"
    elif '==' in condition:
        eq_parts = condition.split("==")
        pass
        if len(eq_parts) > 1:
            return f"{' == '.join(parse_condition(part) for part in eq_parts)}"
    elif "'" in condition:
        # 处理数字常量
        # Check if condition is a signal or a constant
        str_replace = condition
        for signal_constant in constants_list:
            if signal_constant in condition:
                # Replace constant with a variable
                if "'b" in signal_constant:
                    lhs = signal_constant.split("'b")[0]
                    rhs = signal_constant.split("'b")[1]
                    pass
                    data_width = int(lhs)    # 取出数据宽度,int类型
                    data_value = int(rhs,2)    # 取出数据值,int类型
                    str_replace = re.sub(signal_constant, f"BitVecVal({data_value}, {data_width})", str_replace)
                if "'d" in signal_constant:
                    data_width = int(signal_constant.split("'d")[0])    # 取出数据宽度,int类型
                    data_value = int(signal_constant.split("'d")[1])    # 取出数据值,int类型
                    str_replace = re.sub(signal_constant, f"BitVecVal({data_value}, {data_width})", str_replace)
                if "'h" in signal_constant:
                    data_width = int(signal_constant.split("'h")[0])    # 取出数据宽度,int类型
                    data_value = int(signal_constant.split("'h")[1],16)    # 取出数据值,int类型
                    str_replace = re.sub(signal_constant, f"BitVecVal({data_value}, {data_width})", str_replace)
        return parse_condition(str_replace)
    pass 
    # 处理位拼接 `{a, b, c}`
    concat_match = re.findall(r'\{([^}]+)\}', condition)
    for concat_expr in concat_match:
        concat_parts = [parse_condition(part.strip()) for part in concat_expr.split(',')]
        condition = condition.replace(f'{{{concat_expr}}}', f"Concat({', '.join(concat_parts)})")    
    # 处理位选 `a[7:0]` 和 `b[5]`
    bit_select_match = re.findall(r'([a-zA-Z_]\w*)\[(\d+)(?::(\d+))?\]', condition)
    for var, msb, lsb in bit_select_match:
        if lsb is None:
            condition = condition.replace(f'{var}[{msb}]', f'Extract({msb}, {msb}, {var})')
        else:
            condition = condition.replace(f'{var}[{msb}:{lsb}]', f'Extract({msb}, {lsb}, {var})')
    
    # # 处理单个信号（自动转换为布尔条件）
    # if re.match(r'^[a-zA-Z_]\w*$', condition):
    #     return f"{condition} == BitVecVal(1, 1)"  # 假设信号为 1 位
    
    return condition

# Parse Verilog action (e.g., "a <= 2'b0; b <= c? 2'b1 : d;")
def parse_action(action):          # action为字符串
    # initial output
    action = action.strip()                   # 去除两端空格
    signal_pattern = r'(?<!\')\b[a-zA-Z_]\w*\b'             # 匹配信号，但排除以单引号开头的数字常量
    constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量
    signals_in_action = re.findall(signal_pattern, action)
    constants_list = re.findall(constant_pattern, action)    # 动作语句中的数字常量列表
    signal_list_action = signals_in_action                   # 动作语句中的相关信号列表
    pass
    # Create Z3 constraints for action
    if '=' in action:
        action = re.sub(r'<=|=', '==', action)
        action_parts = action.split('==')
        if len(action_parts) > 1:
            return f"{' == '.join(parse_action(part) for part in action_parts)}"
        pass
    elif "'" in action:
        # Check if action is a signal or a constant
        str_replace = action
        for signal_constant in constants_list:
            if signal_constant in action:
                # Replace constant with a variable
                if "'b" in signal_constant:
                    lhs = signal_constant.split("'b")[0]
                    rhs = signal_constant.split("'b")[1]
                    pass
                    data_width = int(lhs)    # 取出数据宽度,int类型
                    data_value = int(rhs,2)    # 取出数据值,int类型
                    str_replace = re.sub(signal_constant, f"BitVecVal({data_value}, {data_width})", str_replace)
                if "'d" in signal_constant:
                    data_width = int(signal_constant.split("'d")[0])    # 取出数据宽度,int类型
                    data_value = int(signal_constant.split("'d")[1])    # 取出数据值,int类型
                    str_replace = re.sub(signal_constant, f"BitVecVal({data_value}, {data_width})", str_replace)
                if "'h" in signal_constant:
                    data_width = int(signal_constant.split("'h")[0])    # 取出数据宽度,int类型
                    data_value = int(signal_constant.split("'h")[1],16)    # 取出数据值,int类型
                    str_replace = re.sub(signal_constant, f"BitVecVal({data_value}, {data_width})", str_replace)
        return parse_action(str_replace)
    pass
    # 处理位拼接 `{a, b, c}`
    concat_match = re.findall(r'\{([^}]+)\}', action)
    for concat_expr in concat_match:
        concat_parts = [parse_action(part.strip()) for part in concat_expr.split(',')]
        action = action.replace(f'{{{concat_expr}}}', f"Concat({', '.join(concat_parts)})")    
    # 处理位选 `a[7:0]` 和 `b[5]`
    bit_select_match = re.findall(r'([a-zA-Z_]\w*)\[(\d+)(?::(\d+))?\]', action)
    for var, msb, lsb in bit_select_match:
        if lsb == '' or lsb == None:
            action = action.replace(f'{var}[{msb}]', f'Extract({msb}, {msb}, {var})')
        else:
            action = action.replace(f'{var}[{msb}:{lsb}]', f'Extract({msb}, {lsb}, {var})')
        pass
    return action

# Main function to convert Verilog constraints to Z3 constraints
def verilog_to_z3(constraint_stack, signals_inout, signals_midle):      
#signals_inout, signals_midle are dictionaries of VerilogSignal objects
    z3_constraints = []
    list_signals_inconstraint = []

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

            if left_signal in right_segment:
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
constraint_stack2 = ["(state) == 2'd1",  "!(tagcomp_miss & biudata_valid) == 1'b1", '(!icqmem_cycstb_i && !last_eval_miss)', "state <= 2'd1;saved_addr_r <= start_addr;hitmiss_eval <= 1'b1;load <= 1'b1;cache_inhibit <= icqmem_ci_i;last_eval_miss <= 0;"]


rst = BitVec('rst', 1)
ic_en = BitVec('ic_en', 1)
icqmem_cycstb_i = BitVec('icqmem_cycstb_i', 1)
icqmem_ci_i = BitVec('icqmem_ci_i', 1)
tagcomp_miss = BitVec('tagcomp_miss', 1)
biudata_valid = BitVec('biudata_valid', 1)
biudata_error = BitVec('biudata_error', 1)
start_addr = BitVec('start_addr', 32)
saved_addr = BitVec('saved_addr', 32)
icram_we = BitVec('icram_we', 4)
biu_read = BitVec('biu_read', 1)
first_hit_ack = BitVec('first_hit_ack', 1)
first_miss_ack = BitVec('first_miss_ack', 1)
first_miss_err = BitVec('first_miss_err', 1)
burst = BitVec('burst', 1)
tag_we = BitVec('tag_we', 1)
state = BitVec('state', 2)
cnt = BitVec('cnt', 4)
saved_addr_r = BitVec('saved_addr_r', 32)
hitmiss_eval = BitVec('hitmiss_eval', 1)
load = BitVec('load', 1)
cache_inhibit = BitVec('cache_inhibit', 1)
last_eval_miss = BitVec('last_eval_miss', 1)
temp_addr = BitVec('temp_addr', 32)

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