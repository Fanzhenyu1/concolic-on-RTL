from z3 import *
import re
from verilog2z3 import parse_condition
from pathlib import Path
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

def generate_constraints_code(cycles_config, cdfg_dict_name="CDFG_dict"):
    code_blocks = []
    
    for config in cycles_config:
        # 生成条件表达式
        conditions = [f"{cdfg_dict_name}['{key}']['condition']" 
                     for key in config['condition_keys']]
        conditions_str = ", ".join(conditions)
        
        # 生成赋值表达式
        actions = [f"{cdfg_dict_name}['{key}']['action']" 
                  for key in config['action_keys']]
        actions_str = ",\n            ".join(actions)
        
        # 构建完整代码块
        code = f"""    # 周期{config['cycle']}约束
    automator.add_verilog_constraints(
        cycle={config['cycle']},
        verilog_conditions=[{conditions_str}],
        verilog_assignments=[
            {actions_str}
        ]
    )"""
        code_blocks.append(code)
    
    return "\n\n".join(code_blocks)

def constraint_build_solver(log_path=None):
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
    # 周期0约束
    automator.add_verilog_constraints(
        cycle=0,
        verilog_conditions=[CDFG_dict['2,1,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['2,1,0,1']['action']
        ]
    )

    # 周期1约束
    automator.add_verilog_constraints(
        cycle=1,
        verilog_conditions=[CDFG_dict['2,1,0,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['2,1,0,0,1']['action']
        ]
    )

    # 周期2约束
    automator.add_verilog_constraints(
        cycle=2,
        verilog_conditions=[CDFG_dict['2,1,0,0,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['2,1,0,0,0,1']['action'],
            CDFG_dict['0,0']['action'],
            CDFG_dict['1,0']['action']
        ]
    )

    # 周期3约束
    automator.add_verilog_constraints(
        cycle=3,
        verilog_conditions=[CDFG_dict['3,1,0,1']['condition']],
        verilog_assignments=[

        ]
    )

    # 查看自动化生成的SMT断言
    print("SMT-LIB格式的约束:\n", automator.get_solver_assertions())

    # 创建文件处理器
    def create_file_handler(path):
        from pathlib import Path
        
        # 确保目录存在
        log_dir = Path(path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建文件并返回句柄
        return open(path, 'w', encoding='utf-8')
    # 输出控制逻辑
    if log_path:
        log_file = create_file_handler(log_path)
        print(f"Logging to {log_path}")
    else:
        log_file = None

    # 执行求解
    if automator.solver.check() == sat:
        model = automator.solver.model()
        
        # 获取输入信号列表
        input_signals = unroller.get_signal_category('inputs')
        
        try:
            # 解析并打印输入激励
            header = "生成的输入激励序列："
            if log_file:
                print(header, file=log_file)
            else:
                print(header)

            for cycle in range(unroller.num_cycles):
                syms = unroller.get_cycle_symbols(cycle)
                cycle_info = []

                # 构建周期头部信息
                cycle_info.append(f"\nCycle {cycle}:")

                # 仅输出输入信号
                for sig in input_signals:
                    val = model.evaluate(syms[sig])
                    if isinstance(val, BitVecNumRef):
                        hex_value = f"0x{val.as_long():X}"
                        line = f"  {sig.ljust(6)} = {val} ({hex_value})"
                    else:
                        line = f"  {sig.ljust(6)} = {val} ([未完全约束])"
                    cycle_info.append(line)

                # 输出到目标
                output = '\n'.join(cycle_info)
                if log_file:
                    print(output, file=log_file)
                    log_file.flush()  # 确保及时写入
                else:
                    print(output)

        finally:
            # 资源清理
            if log_file:
                log_file.close()
    else:
        print("无解！约束存在冲突")

def log_to_config(log_path, target_signals=['in']):
    signal_pattern = re.compile(
        r'^(?P<signal>\w+)\s*=\s*(?P<value>\S+).*?\((?P<comment>[^)]+)\)$'
    )
    config = []
    current_cycle = -1
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 周期检测
            if line.startswith("Cycle "):
                current_cycle = int(line.split()[1].rstrip(':'))
                config.append({sig: None for sig in target_signals})
                continue
            
            # 信号解析（仅在有效周期内处理）
            if current_cycle >= 0 and line:
                match = signal_pattern.match(line)
                if match:
                    sig_info = match.groupdict()
                    sig_name = sig_info['signal']
                    
                    if sig_name in target_signals:
                        # 数值解析逻辑
                        value = None
                        
                        # 情况1：注释包含十六进制值
                        hex_match = re.search(r'0x([0-9A-Fa-f]+)', sig_info['comment'])
                        if hex_match:
                            value = int(hex_match.group(1), 16)
                        
                        # 情况2：值字段为数字
                        elif sig_info['value'].isdigit():
                            value = int(sig_info['value'])
                        
                        # 情况3：未约束标记
                        elif '[未完全约束]' in sig_info['comment']:
                            value = None
                        
                        config[current_cycle][sig_name] = value

    return config

def generate_testbench(cycles, signal_def):
    # 生成输入信号列表（排除clk/rst）
    input_signals = []
    for sig, (io_type, width) in signal_def.items():
        if io_type == 1 and sig not in (clk_name, rst_name):
            if sig not in input_signals:
                input_signals.append(sig)  # 保持原始顺序
    
    tb_code = []
    for cycle_num, cycle in enumerate(cycles):
        signals = []
        for sig in input_signals:
            width = signal_def[sig][1]  # 获取位宽
            
            # 处理信号赋值
            if sig in cycle:
                value = cycle[sig]
                if value is None:
                    signals.append(f"{sig} = $random;")
                else:
                    # 应用位宽掩码并生成十进制
                    masked = value & ((1 << width) - 1)
                    signals.append(f"{sig} = {width}'d{masked};")
            else:
                signals.append(f"{sig} = $random;")
        
        # 添加时间控制
        signals.append("#10;")
        
        # 合并周期代码
        tb_code.append(f"// Cycle {cycle_num}\n    " + "\n    ".join(signals))
    
    return "\n\n".join(tb_code)

# -------------------------------------------------
def main():
    # 路径设置
    path_config = [
        {
            'cycle': 0,
            'condition_keys': ['2,1,0,1'],
            'action_keys': ['2,1,0,1']
        },        
        {
            'cycle': 1,
            'condition_keys': ['2,1,0,0,1'],
            'action_keys': ['2,1,0,0,1']
        },        
        {
            'cycle': 2,
            'condition_keys': ['2,1,0,0,0,1'],
            'action_keys': ['2,1,0,0,0,1', '0,0', '1,0']
        },
        {
            'cycle': 3,
            'condition_keys': ['3,1,0,1'],
            'action_keys': []
        }
    ]
    # 约束代码生成
    generated_code = generate_constraints_code(path_config)
    print(generated_code)

    log_path="./RTL/case1/constraint_solve.log"
    # # 约束建立&求解
    constraint_build_solver(log_path)

    sim_config = log_to_config(log_path)
    print(sim_config)
    # # sim_config = [
    # #     {"input_a": 287454020, "input_b": None, "ctr": None},
    # #     {"input_a": 2578103244, "input_b": 3721195263, "ctr": 305419896},
    # #     {"input_a": None, "input_b": 1432778632, "ctr": None},
    # #     {"input_a": None, "input_b": None, "ctr": None},
    # #     {"input_a": None, "input_b": None, "ctr": None}
    # # ]
    # # 激励文本生成
    gen_sim = generate_testbench(sim_config, signal_def)
    print(gen_sim)


# ---------------------------
# 使用示例
# ---------------------------
if __name__ == "__main__":
    # 定义clk和rst name
    clk_name = 'clk'
    rst_name = 'rst'

    signal_def = {'in': (1, 8), 'out': (3, 8), 'clk': (1, 1), 'rst': (1, 1), 'state': (2, 4), 'st': (2, 4), 'st2': (2, 4)}

    CDFG_list = [{'0,0': {'condition': '', 'action': "st = state + 4'd2;", 'block_path': ['0,0']}}, {'1,0': {'condition': '', 'action': 'st2 = st;', 'block_path': ['1,0']}}, {'2,1': {'condition': '', 'action': '', 'block_path': ['2,1']}, '2,1,1': {'condition': "(rst) == 1'b1", 'action': "state <= 4'h0;", 'block_path': ['2,1', '2,1,1']}, '2,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['2,1', '2,1,0']}, '2,1,0,1': {'condition': "(in == 8'h26)", 'action': "state <= 4'h1;", 'block_path': ['2,1', '2,1,0', '2,1,0,1']}, '2,1,0,0': {'condition': "!(in == 8'h26)", 'action': '', 'block_path': ['2,1', '2,1,0', '2,1,0,0']}, '2,1,0,0,1': {'condition': "(in == 8'hf5 && state == 4'h1)", 'action': "state <= 4'h2;", 'block_path': ['2,1', '2,1,0', '2,1,0,0', '2,1,0,0,1']}, '2,1,0,0,0': {'condition': "!(in == 8'hf5 && state == 4'h1)", 'action': '', 'block_path': ['2,1', '2,1,0', '2,1,0,0', '2,1,0,0,0']}, '2,1,0,0,0,1': {'condition': "(in == 8'h6e && state == 4'h2)", 'action': "state <= 4'h3;", 'block_path': ['2,1', '2,1,0', '2,1,0,0', '2,1,0,0,0', '2,1,0,0,0,1']}, '2,1,0,0,0,0': {'condition': "!(in == 8'h6e && state == 4'h2)", 'action': "state <= 4'h0;", 'block_path': ['2,1', '2,1,0', '2,1,0,0', '2,1,0,0,0', '2,1,0,0,0,0']}}, {'3,1': {'condition': '', 'action': '', 'block_path': ['3,1']}, '3,1,1': {'condition': "(rst) == 1'b1", 'action': "out <= 8'b0;", 'block_path': ['3,1', '3,1,1']}, '3,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['3,1', '3,1,0']}, '3,1,0,1': {'condition': "(st2 == 4'h5)", 'action': 'out <= 1;', 'block_path': ['3,1', '3,1,0', '3,1,0,1']}}]
    main()
