from z3 import *
import re
import random
##input: verilog path constraint stack, signal list [a,b] || condition, such as "a==b", action, such as "a <= 2'b0;"
##output: Z3 solver constraint
import path_reduction


target_path_C, constraint_stack_list = path_reduction.main()
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
    if condition.startswith('!'):
        condition_new = condition[1:] + " == 1'b1"
        return f"Not({parse_condition(condition_new)})"
    elif condition.startswith('(') and condition.endswith(')'):
        return parse_condition(condition[1:-1])
    elif '||' in condition:
        or_parts = condition.split("||")
        if len(or_parts) > 1:
            return f"Or({', '.join(parse_condition(part) for part in or_parts)})"
    elif '&&' in condition:  
        and_parts = condition.split("&&")
        if len(and_parts) > 1:
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
        if len(eq_parts) > 1:
            return f"{' == '.join(parse_condition(part) for part in eq_parts)}"
    else:
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
        return str_replace

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
    else:
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
        return str_replace
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
constraint_stack1 = ["r_in == 6'b101010", "a <= r_in;", "b < a & 6'b100100", "b <= 6'b100110"]

# Define Z3 BitVec variables for each signal
# r_in = BitVec('r_in', 6)
# a = BitVec('a', 6)
# b = BitVec('b', 6)
# signal_inout = {'r_in': [r_in, 6], 'a': [a, 6], 'b': [b, 6]}
in_1 = BitVec('in_1', 8)
clk = BitVec('clk', 1)
rst = BitVec('rst', 1)
out = BitVec('out', 8)
state = BitVec('state', 4)
st = BitVec('st', 4)
st2 = BitVec('st2', 4)


for i in range(len(constraint_stack_list)):
    constraint_stack = constraint_stack_list[i]
    solver = Solver()
    main_z3_solver(constraint_stack, {}, {})
    if solver.check() == sat:
        print("Constraints are satisfiable.")
    else:
        target_path_C[i] = []
        print("Constraints are unsatisfiable.")

# Create Z3 solver and add constraints
# main_z3_solver(constraint_stack1, signal_inout, {})
###############################-----------------------------###############