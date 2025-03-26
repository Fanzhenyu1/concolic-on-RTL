from z3 import *
import re
from verilog2z3 import parse_condition

class SignalUnroller:
    def __init__(self, signal_inout, num_cycles=3):
        """
        :param signal_inout: 信号类型字典，格式如 {'clk':1, 'state':2}
                            值表示信号类型：1=input, 2=state, 3=output
        :param num_cycles: 需要展开的周期数
        """
        self.num_cycles = num_cycles
        self.signal_def = signal_inout
        self.cycles = []          # 存储各周期的符号字典
        self.signal_categories = {
            'inputs': [],
            'states': [],
            'outputs': []
        }
        
        # 生成所有周期的符号变量
        self._unroll_signals()
    
    def _unroll_signals(self):
        """核心展开函数"""
        for cycle in range(self.num_cycles):
            cycle_syms = {}
            for sig_name, (sig_type, width) in self.signal_def.items():
                # 生成带周期后缀的符号名（如clk_0, state_1）
                sym_name = f"{sig_name}__{cycle}"
                sym = BitVec(sym_name, width)
                cycle_syms[sig_name] = sym
                
                # 分类记录信号
                if cycle == 0:  # 只需在首周期记录一次
                    if sig_type == 1:
                        self.signal_categories['inputs'].append(sig_name)
                    elif sig_type == 2:
                        self.signal_categories['states'].append(sig_name)
                    elif sig_type == 3:
                        self.signal_categories['outputs'].append(sig_name)
            
            self.cycles.append(cycle_syms)
    
    def get_cycle_symbols(self, cycle):
        """获取指定周期的符号字典"""
        return self.cycles[cycle]
    
    def get_all_symbols(self):
        """获取所有周期的符号字典列表"""
        return self.cycles
    
    def get_signal_category(self, category):
        """获取指定类别的信号列表"""
        return self.signal_categories.get(category, [])


class MultiCycleConstraintManager:
    def __init__(self, unroller):
        """
        :param unroller: SignalUnroller实例，提供符号化变量
        """
        self.unroller = unroller
        self.solver = Solver()
        self.constraints = []
        
    def add_generic_constraint(self, constraint):
        """添加任意类型的约束"""
        self.constraints.append(constraint)
        
    def add_cycle_constraint(self, cycle, constraint_fn):
        """
        添加特定周期的约束
        :param cycle: 目标周期号
        :param constraint_fn: 函数格式 lambda sym: expression
        """
        syms = self.unroller.get_cycle_symbols(cycle)
        self.constraints.append(constraint_fn(syms))
    
    def add_cross_cycle_constraint(self, prev_cycle, curr_cycle, constraint_fn):
        """
        添加跨周期约束（时序逻辑）
        :param prev_cycle: 前一周期的符号
        :param curr_cycle: 当前周期的符号
        :param constraint_fn: 函数格式 lambda prev, curr: expression
        """
        prev_syms = self.unroller.get_cycle_symbols(prev_cycle)
        curr_syms = self.unroller.get_cycle_symbols(curr_cycle)
        self.constraints.append(constraint_fn(prev_syms, curr_syms))
    
    def add_input_constraints(self, constraint_fn):
        """
        添加所有输入信号的约束
        :param constraint_fn: 函数格式 lambda inputs: expression
        """
        for cycle in range(self.unroller.num_cycles):
            syms = self.unroller.get_cycle_symbols(cycle)
            inputs = {name: syms[name] for name in self.unroller.get_signal_category('inputs')}
            self.constraints.append(constraint_fn(inputs))
    
    def add_reset_constraints(self, active_cycles):
        """
        添加复位约束
        :param active_cycles: 需要保持复位的周期列表
        """
        for cycle in active_cycles:
            syms = self.unroller.get_cycle_symbols(cycle)
            self.constraints.append(syms['rst'] == BitVecVal(1, 1))
    
    def solve_and_validate(self):
        """执行求解并返回结果"""
        self.solver.add(self.constraints)
        if self.solver.check() == sat:
            model = self.solver.model()
            return self._parse_solution(model)
        else:
            return None
    
    def _parse_solution(self, model):
        """解析求解结果为可读格式"""
        solution = []
        for cycle in range(self.unroller.num_cycles):
            syms = self.unroller.get_cycle_symbols(cycle)
            cycle_solution = {}
            for name in syms:
                cycle_solution[name] = model.evaluate(syms[name])
            solution.append(cycle_solution)
        return solution

class ConstraintAutomator:
    def __init__(self, unroller):
        self.unroller = unroller  # SignalUnroller实例
        self.solver = Solver()
        
    def add_verilog_constraints(self, cycle, verilog_conditions=[], verilog_assignments=[]):
        """
        集成Verilog解析器的约束添加方法
        :param cycle: 当前周期号
        :param verilog_conditions: Verilog条件列表 ["a == 1'b1", "b && c"]
        :param verilog_assignments: Verilog赋值列表 ["d <= 2'h3", "e = f + g"]
        """
        curr_syms = self.unroller.get_cycle_symbols(cycle)
        next_cycle = cycle + 1
        
        # 处理条件约束
        for cond in verilog_conditions:
            z3_expr = self._parse_verilog_condition(cond, curr_syms)
            self.solver.add(z3_expr)
        
        # 处理赋值约束
        for assign in verilog_assignments:
            if '<=' in assign:  # 非阻塞赋值
                if next_cycle >= self.unroller.num_cycles:
                    continue
                next_syms = self.unroller.get_cycle_symbols(next_cycle)
                self._process_nonblocking_assign(assign, curr_syms, next_syms)
            else:  # 阻塞赋值
                self._process_blocking_assign(assign, curr_syms)

    def _parse_verilog_condition(self, condition, syms_dict):
        """集成你的parse_condition函数"""
        # 替换信号名为当前周期符号
        for sig in syms_dict:
            condition = re.sub(r'\b' + sig + r'\b', f'syms_dict["{sig}"]', condition)
        
        # 生成Z3表达式对象
        parsed_str = parse_condition(condition)
        # 定义所有需要的Z3函数
        z3_env = {
            'And': And,
            'Or': Or,
            'Not': Not,
            'If': If,
            'Extract': Extract,
            'Concat': Concat,
            'BitVecVal': BitVecVal,
            'syms_dict': syms_dict
        }
        return eval(parsed_str, {}, z3_env)

    def _process_nonblocking_assign(self, assignment, curr_syms, next_syms):
        """处理非阻塞赋值（带周期符号替换）"""
        # 使用你的parse_action函数
        lhs, rhs = self._parse_assignment(assignment)
        parsed_rhs = parse_condition(rhs, in_comparison=True)
        
        # 替换当前周期符号
        for sig in curr_syms:
            parsed_rhs = re.sub(r'\b' + sig + r'\b', f'curr_syms["{sig}"]', parsed_rhs)
        
        # 生成约束表达式
        rhs_expr = eval(parsed_rhs, {'curr_syms': curr_syms, 'BitVecVal': BitVecVal})
        self.solver.add(next_syms[lhs] == rhs_expr)

    def _process_blocking_assign(self, assignment, curr_syms):
        """处理阻塞赋值（兼容布尔表达式）"""
        lhs, rhs = self._parse_assignment(assignment)
        parsed_rhs = parse_condition(rhs, in_comparison=True)
        
        # 替换当前周期符号
        for sig in curr_syms:
            parsed_rhs = re.sub(r'\b' + sig + r'\b', f'curr_syms["{sig}"]', parsed_rhs)
        
        # 生成约束表达式
        rhs_expr = eval(parsed_rhs, {'curr_syms': curr_syms, 'BitVecVal': BitVecVal})
        
        # 获取左侧位宽
        lhs_width = self.unroller.signal_def[lhs][1]
        
        # 处理右侧表达式类型
        if isinstance(rhs_expr, BoolRef):
            # 将布尔表达式转换为1-bit BitVec
            rhs_expr = If(rhs_expr, BitVecVal(1, 1), BitVecVal(0, 1))
            rhs_width = 1
        else:
            rhs_width = rhs_expr.size()
        
        # 位宽适配
        if lhs_width != rhs_width:
            if rhs_width < lhs_width:
                # 零扩展
                rhs_expr = ZeroExt(lhs_width - rhs_width, rhs_expr)
            else:
                # 截断高位
                rhs_expr = Extract(lhs_width-1, 0, rhs_expr)
        
        # 添加约束
        self.solver.add(curr_syms[lhs] == rhs_expr)

    def _parse_assignment(self, assignment):
        """集成你的parse_action核心逻辑"""
        assignment = assignment.strip().rstrip(';')
        if '<=' in assignment:
            lhs, rhs = assignment.split('<=', 1)
            return lhs.strip(), rhs.strip()
        else:
            lhs, rhs = assignment.split('=', 1)
            return lhs.strip(), rhs.strip()

def main():
    # 实例化信号展开器
    unroller = SignalUnroller(signal_def, num_cycles=5)
    
    # 实例化约束管理器
    automator = ConstraintAutomator(unroller)
    # 添加多周期约束
    # ---------------------------------------------------
    # 周期0约束：复位信号有效
    automator.add_verilog_constraints(
        cycle=0,
        verilog_conditions=["rst == 1'b1"],
        verilog_assignments=["count <= 2'b0"]
    )

    # 周期1约束：复位无效，启用计数器
    automator.add_verilog_constraints(
        cycle=1,
        verilog_conditions=["rst == 1'b0 && enable == 1'b1"],
        verilog_assignments=[
            "count <= count + 1",  # 非阻塞赋值，周期2生效
            "trigger = (count == 2'b10)"  # 阻塞赋值，立即生效
        ]
    )

    # 周期2约束：持续计数
    automator.add_verilog_constraints(
        cycle=2,
        verilog_assignments=[
            "count <= count + 1",
            "trigger = (count == 2'b11)"
        ]
    )

    # 执行求解
    if automator.solver.check() == sat:
        model = automator.solver.model()
        
        # 获取输入信号列表
        input_signals = unroller.get_signal_category('inputs')
        
        # 解析并打印输入激励
        print("生成的输入激励序列：")
        for cycle in range(unroller.num_cycles):
            syms = unroller.get_cycle_symbols(cycle)
            print(f"\nCycle {cycle}:")
            
            # 仅输出输入信号
            for sig in input_signals:
                val = model.evaluate(syms[sig])
                if isinstance(val, BitVecNumRef):
                    hex_value = f"0x{val.as_long():X}"
                else:
                    hex_value = "[未完全约束]"
                print(f"  {sig.ljust(6)} = {val} ({hex_value})")
    else:
        print("无解！约束存在冲突")

# -------------------------------------------------

# ---------------------------
# 使用示例
# ---------------------------
if __name__ == "__main__":
    signal_def = {
        'rst': (1, 1),       # 输入，1-bit
        'enable': (1, 1),    # 输入，1-bit
        'count': (2, 2),     # 状态寄存器，4-bit
        'trigger': (3, 1)    # 输出，1-bit
    }
    main()
