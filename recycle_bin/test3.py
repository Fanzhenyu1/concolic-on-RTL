from z3 import *

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
# ---------------------------
# 使用示例
# ---------------------------
if __name__ == "__main__":
    # 输入信号类型定义（值格式：元组（类型，位宽））
    signal_inout = {
        'rst': (1, 1),       # 1=input，1位
        'input_a': (1, 32),
        'input_b': (1, 32),
        'ctr': (2, 32),      # 2=state，32位
        'ctr_1': (2, 32),
        'ctr_2': (2, 32),
        'signal1': (2, 1),
        'signal2': (2, 1),
        'signal3': (2, 1),
        'trigger': (3, 1),  # 3=output，1位
        'ht_out': (3, 32)
    }
    
    # 创建展开器（展开3个周期）
    unroller = SignalUnroller(signal_inout, num_cycles=3)
    
    # 获取所有周期符号
    all_cycles = unroller.get_all_symbols()
    print(all_cycles)
    print("\nAll Cycles:")
    for cycle, cycle_syms in enumerate(all_cycles):
        print(f"Cycle {cycle+1}:")
        for name, sym in cycle_syms.items():
            print(f"{name}: {sym}")
    # 获取所有输入信号列表
    print("\nInput Signals:", unroller.get_signal_category('inputs'))