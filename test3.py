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
        """解析Verilog条件，并对1位信号做条件包装（如果不是参与比较则包装为布尔判断）"""
        # 针对每个信号进行替换
        for sig, (sig_type, width) in self.unroller.signal_def.items():
            pattern = r'\b' + re.escape(sig) + r'\b'
            if width == 1:
                # 使用自定义函数进行替换，根据前后字符判断是否参与比较
                def repl(m):
                    # m.string为原始字符串，m.start()和m.end()为匹配位置
                    s = m.string
                    start, end = m.start(), m.end()
                    # 查看匹配项前后的若干字符（这里取3个字符作为上下文，可根据需要调整）
                    prefix = s[max(0, start-3):start]
                    suffix = s[end:end+3]
                    # 如果前后含有 '==' 则视为比较中，不再包装
                    if '==' in prefix or '==' in suffix:
                        return f'syms_dict["{sig}"]'
                    else:
                        return f'(syms_dict["{sig}"] == BitVecVal(1,1))'
                condition = re.sub(pattern, repl, condition)
            else:
                # 非1位信号直接替换
                condition = re.sub(pattern, f'syms_dict["{sig}"]', condition)
        
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
        pass
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
    
    def get_solver_assertions(self):
        """获取求解器中的SMT-LIB格式断言"""
        return self.solver.to_smt2()

def main():
    # 字典列表转化
    CDFG_dict = {}
    CDFG_dict = {k: v for CDFG in CDFG_list for k, v in CDFG.items()}
    print(CDFG_dict)

    # 实例化信号展开器
    unroller = SignalUnroller(signal_def, num_cycles=5)
    
    # 实例化约束管理器
    automator = ConstraintAutomator(unroller)

    # 添加多周期约束
    # ---------------------------------------------------
    # 周期0约束：
    automator.add_verilog_constraints(
        cycle=0,
        verilog_conditions=[CDFG_dict['1,1,0,1']['condition']],
        verilog_assignments=[CDFG_dict['1,1,0,1']['action']]
    )

    # 周期1约束：
    automator.add_verilog_constraints(
        cycle=1,
        verilog_conditions=[CDFG_dict['1,1,0,0,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['1,1,0,0,0,1']['action'],  # 非阻塞赋值，周期2生效
            CDFG_dict['2,1']['action']  # 阻塞赋值，立即生效
        ]
    )

    # 周期2约束：
    automator.add_verilog_constraints(
        cycle=2,
        verilog_conditions=[CDFG_dict['1,1,0,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['1,1,0,0,1']['action'],
            CDFG_dict['0,0']['action'],
            CDFG_dict['3,1']['action']
        ]
    )

    # 周期3约束：
    automator.add_verilog_constraints(
        cycle=3,
        verilog_conditions=[CDFG_dict['4,1,0,1,1']['condition']],
        verilog_assignments=[]
    )

    # 查看自动化生成的SMT断言
    print("SMT-LIB格式的约束:\n", automator.get_solver_assertions())

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
    signal_def = {'clk': (1, 1), 'rst': (1, 1), 'input_a': (1, 32), 'input_b': (1, 32), 'ctr': (1, 32), 'ht_out': (3, 32), 'signal1': (2, 1), 'signal2': (2, 1), 'signal3': (2, 1), 'ctr_1': (2, 32), 'ctr_2': (2, 32), 'trigger': (2, 1)}
    CDFG_list = [{'0,0': {'condition': '', 'action': 'trigger = signal1 & signal2 & signal3;', 'block_path': ['0,0']}}, {'1,1': {'condition': '', 'action': '', 'block_path': ['1,1']}, '1,1,1': {'condition': "(rst) == 1'b1", 'action': "signal1 <= 1'b0;signal2 <= 1'b0;signal3 <= 1'b0;", 'block_path': ['1,1', '1,1,1']}, '1,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['1,1', '1,1,0']}, '1,1,0,1': {'condition': "(input_a == 32'h11223344)", 'action': "signal2 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,1']}, '1,1,0,0': {'condition': "!(input_a == 32'h11223344)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,0']}, '1,1,0,0,1': {'condition': "(input_b == 32'h55667788 && signal1)", 'action': "signal3 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,1']}, '1,1,0,0,0': {'condition': "!(input_b == 32'h55667788 && signal1)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0']}, '1,1,0,0,0,1': {'condition': "(input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2)", 'action': "signal1 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0', '1,1,0,0,0,1']}, '1,1,0,0,0,0': {'condition': "!(input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2)", 'action': "signal1 <= 1'b0;signal2 <= 1'b0;signal3 <= 1'b0;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0', '1,1,0,0,0,0']}}, {'2,1': {'condition': '', 'action': 'ctr_1 <= ctr;', 'block_path': ['2,1']}}, {'3,1': {'condition': '', 'action': 'ctr_2 <= ctr_1;', 'block_path': ['3,1']}}, {'4,1': {'condition': '', 'action': '', 'block_path': ['4,1']}, '4,1,1': {'condition': "(rst) == 1'b1", 'action': "ht_out <= 32'b0;", 'block_path': ['4,1', '4,1,1']}, '4,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['4,1', '4,1,0']}, '4,1,0,1': {'condition': "(ctr_2 == 32'h12345678)", 'action': '', 'block_path': ['4,1', '4,1,0', '4,1,0,1']}, '4,1,0,1,1': {'condition': "(trigger == 1'b1)", 'action': "ht_out <= {ht_out[30:0], ht_out[31] ^ 1'b1};", 'block_path': ['4,1', '4,1,0', '4,1,0,1', '4,1,0,1,1']}, '4,1,0,1,0': {'condition': "!(trigger == 1'b1)", 'action': 'ht_out <= {ht_out[30:0], ht_out[31]};', 'block_path': ['4,1', '4,1,0', '4,1,0,1', '4,1,0,1,0']}, '4,1,0,0': {'condition': "!(ctr_2 == 32'h12345678)", 'action': 'ht_out <= ht_out;', 'block_path': ['4,1', '4,1,0', '4,1,0,0']}}] 
    main()
