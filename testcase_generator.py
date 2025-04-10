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
        
        new_assignments = [s.strip() for assignment in verilog_assignments 
                           for s in assignment.split(';') 
                           if s.strip() != '']
        # 处理赋值约束
        for assign in new_assignments:
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
    # 周期0约束
    automator.add_verilog_constraints(
        cycle=0,
        verilog_conditions=[CDFG_dict['0,0,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['0,0,0,1']['action']
        ]
    )

    # 周期1约束
    automator.add_verilog_constraints(
        cycle=1,
        verilog_conditions=[CDFG_dict['0,0,0,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['0,0,0,0,1']['action']
        ]
    )

    # 周期2约束
    automator.add_verilog_constraints(
        cycle=2,
        verilog_conditions=[CDFG_dict['0,0,0,0,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['0,0,0,0,0,1']['action']
        ]
    )

    # 周期3约束
    automator.add_verilog_constraints(
        cycle=3,
        verilog_conditions=[CDFG_dict['0,0,0,0,0,0,1']['condition']],
        verilog_assignments=[
            CDFG_dict['0,0,0,0,0,0,1']['action'],
            CDFG_dict['1,0']['action']
        ]
    )

    # 周期4约束
    automator.add_verilog_constraints(
        cycle=4,
        verilog_conditions=[CDFG_dict['5,1,0,1']['condition']],
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
            'condition_keys': ['0,0,0,1'],
            'action_keys': ['0,0,0,1']
        },        
        {
            'cycle': 1,
            'condition_keys': ['0,0,0,0,1'],
            'action_keys': ['0,0,0,0,1']
        },        
        {
            'cycle': 2,
            'condition_keys': ['0,0,0,0,0,1'],
            'action_keys': ['0,0,0,0,0,1']
        },
        {
            'cycle': 3,
            'condition_keys': ['0,0,0,0,0,0,1'],
            'action_keys': ['0,0,0,0,0,0,1', '1,0']
        },
        {
            'cycle': 4,
            'condition_keys': ['5,1,0,1'],
            'action_keys': []
        }        
    ]
    # 约束代码生成
    generated_code = generate_constraints_code(path_config)
    print(generated_code)

    log_path="./RTL/AES-T1100/constraint_solve.log"
    # # 约束建立&求解
    constraint_build_solver(log_path)

    sim_config = log_to_config(log_path)
    print(sim_config)

    # # # 激励文本生成
    gen_sim = generate_testbench(sim_config, signal_def)
    print(gen_sim)


# ---------------------------
# 使用示例
# ---------------------------
if __name__ == "__main__":
    # 定义clk和rst name
    clk_name = 'clk'
    rst_name = 'rst'

    signal_def = {'clk': (1, 1), 'rst': (1, 1), 'state': (1, 128), 'key': (1, 128), 'Capacitance': (3, 64), 'Tj_Trig': (2, 1), 'State0': (2, 1), 'State1': (2, 1), 'State2': (2, 1), 'State3': (2, 1), 'lfsr_stream': (2, 20), 'lfsr': (2, 20), 'd0': (2, 1), 'data': (2, 128), 'counter': (2, 20), 'load': (2, 64)}

    # CDFG_list = [{'0,1': {'condition': '', 'action': '', 'block_path': ['0,1']}, '0,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "rst_cnt <= 5'h0;", 'block_path': ['0,1', '0,1,1']}, '0,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['0,1', '0,1,0']}, '0,1,0,1': {'condition': "(LineState_o != 2'h0)", 'action': "rst_cnt <= 5'h0;", 'block_path': ['0,1', '0,1,0', '0,1,0,1']}, '0,1,0,0': {'condition': "!(LineState_o != 2'h0)", 'action': '', 'block_path': ['0,1', '0,1,0', '0,1,0,0']}, '0,1,0,0,1': {'condition': '(!(usb_rst) && i_rx_phy_fs_ce)', 'action': "rst_cnt <= (rst_cnt + 5'h1);", 'block_path': ['0,1', '0,1,0', '0,1,0,0', '0,1,0,0,1']}}, {'1,1': {'condition': '', 'action': '', 'block_path': ['1,1']}, '1,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "usb_rst <= 1'b0;", 'block_path': ['1,1', '1,1,1']}, '1,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': "usb_rst <= (rst_cnt == 5'h1f);", 'block_path': ['1,1', '1,1,0']}}, {'2,0': {'condition': '', 'action': 'txdp = i_tx_phy_txdp;', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': 'txdn = i_tx_phy_txdn;', 'block_path': ['3,0']}}, {'4,0': {'condition': '', 'action': 'txoe = i_tx_phy_txoe;', 'block_path': ['4,0']}}, {'5,0': {'condition': '', 'action': 'TxReady_o = i_tx_phy_TxReady_o;', 'block_path': ['5,0']}}, {'6,1': {'condition': '', 'action': '', 'block_path': ['6,1']}, '6,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_TxReady_o <= 1'b0;", 'block_path': ['6,1', '6,1,1']}, '6,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_tx_phy_TxReady_o <= (i_tx_phy_tx_ready_d & TxValid_i);', 'block_path': ['6,1', '6,1,0']}}, {'7,1': {'condition': '', 'action': 'i_tx_phy_ld_data <= i_tx_phy_ld_data_d;', 'block_path': ['7,1']}}, {'8,1': {'condition': '', 'action': '', 'block_path': ['8,1']}, '8,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b0;", 'block_path': ['8,1', '8,1,1']}, '8,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['8,1', '8,1,0']}, '8,1,0,1': {'condition': "(i_tx_phy_ld_sop_d) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b1;", 'block_path': ['8,1', '8,1,0', '8,1,0,1']}, '8,1,0,0': {'condition': "!(i_tx_phy_ld_sop_d) == 1'b1", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,0']}, '8,1,0,0,1': {'condition': "(i_tx_phy_app_eop_sync3) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,0', '8,1,0,0,1']}}, {'9,1': {'condition': '', 'action': '', 'block_path': ['9,1']}, '9,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_tx_ip_sync <= 1'b0;", 'block_path': ['9,1', '9,1,1']}, '9,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['9,1', '9,1,0']}, '9,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_tx_ip_sync <= i_tx_phy_tx_ip;', 'block_path': ['9,1', '9,1,0', '9,1,0,1']}}, {'10,1': {'condition': '', 'action': '', 'block_path': ['10,1']}, '10,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_data_done <= 1'b0;", 'block_path': ['10,1', '10,1,1']}, '10,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['10,1', '10,1,0']}, '10,1,0,1': {'condition': '(TxValid_i && !(i_tx_phy_tx_ip))', 'action': "i_tx_phy_data_done <= 1'b1;", 'block_path': ['10,1', '10,1,0', '10,1,0,1']}, '10,1,0,0': {'condition': '!(TxValid_i && !(i_tx_phy_tx_ip))', 'action': '', 'block_path': ['10,1', '10,1,0', '10,1,0,0']}, '10,1,0,0,1': {'condition': "(!(TxValid_i)) == 1'b1", 'action': "i_tx_phy_data_done <= 1'b0;", 'block_path': ['10,1', '10,1,0', '10,1,0,0', '10,1,0,0,1']}}, {'11,1': {'condition': '', 'action': '', 'block_path': ['11,1']}, '11,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_bit_cnt <= 3'h0;", 'block_path': ['11,1', '11,1,1']}, '11,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['11,1', '11,1,0']}, '11,1,0,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_bit_cnt <= 3'h0;", 'block_path': ['11,1', '11,1,0', '11,1,0,1']}, '11,1,0,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['11,1', '11,1,0', '11,1,0,0']}, '11,1,0,0,1': {'condition': '(i_rx_phy_fs_ce && !(i_tx_phy_stuff))', 'action': "i_tx_phy_bit_cnt <= (i_tx_phy_bit_cnt + 3'h1);", 'block_path': ['11,1', '11,1,0', '11,1,0,0', '11,1,0,0,1']}}, {'12,1': {'condition': '', 'action': '', 'block_path': ['12,1']}, '12,1,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_sd_raw_o <= 1'b0;", 'block_path': ['12,1', '12,1,1']}, '12,1,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['12,1', '12,1,0']}, '12,1,0,1': {'condition': "(i_tx_phy_bit_cnt) == 3'h0", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[0];', 'block_path': ['12,1', '12,1,0', '12,1,0,1']}, '12,1,0,2': {'condition': "(i_tx_phy_bit_cnt) == 3'h1", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[1];', 'block_path': ['12,1', '12,1,0', '12,1,0,2']}, '12,1,0,3': {'condition': "(i_tx_phy_bit_cnt) == 3'h2", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[2];', 'block_path': ['12,1', '12,1,0', '12,1,0,3']}, '12,1,0,4': {'condition': "(i_tx_phy_bit_cnt) == 3'h3", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[3];', 'block_path': ['12,1', '12,1,0', '12,1,0,4']}, '12,1,0,5': {'condition': "(i_tx_phy_bit_cnt) == 3'h4", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[4];', 'block_path': ['12,1', '12,1,0', '12,1,0,5']}, '12,1,0,6': {'condition': "(i_tx_phy_bit_cnt) == 3'h5", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[5];', 'block_path': ['12,1', '12,1,0', '12,1,0,6']}, '12,1,0,7': {'condition': "(i_tx_phy_bit_cnt) == 3'h6", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[6];', 'block_path': ['12,1', '12,1,0', '12,1,0,7']}, '12,1,0,8': {'condition': "(i_tx_phy_bit_cnt) == 3'h7", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[7];', 'block_path': ['12,1', '12,1,0', '12,1,0,8']}}, {'13,1': {'condition': '', 'action': "i_tx_phy_sft_done <= (!((i_tx_phy_one_cnt == 3'h6)) & (i_tx_phy_bit_cnt == 3'h7));", 'block_path': ['13,1']}}, {'14,1': {'condition': '', 'action': 'i_tx_phy_sft_done_r <= i_tx_phy_sft_done;', 'block_path': ['14,1']}}, {'15,1': {'condition': '', 'action': '', 'block_path': ['15,1']}, '15,1,1': {'condition': "(i_tx_phy_ld_sop_d) == 1'b1", 'action': "i_tx_phy_hold_reg <= 8'h80;", 'block_path': ['15,1', '15,1,1']}, '15,1,0': {'condition': "!(i_tx_phy_ld_sop_d) == 1'b1", 'action': '', 'block_path': ['15,1', '15,1,0']}, '15,1,0,1': {'condition': "(i_tx_phy_ld_data) == 1'b1", 'action': 'i_tx_phy_hold_reg <= DataOut_i;', 'block_path': ['15,1', '15,1,0', '15,1,0,1']}}, {'16,1': {'condition': '', 'action': 'i_tx_phy_hold_reg_d <= i_tx_phy_hold_reg;', 'block_path': ['16,1']}}, {'17,1': {'condition': '', 'action': '', 'block_path': ['17,1']}, '17,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,1']}, '17,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0']}, '17,1,0,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,0', '17,1,0,1']}, '17,1,0,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0', '17,1,0,0']}, '17,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1']}, '17,1,0,0,1,1': {'condition': "(!(i_tx_phy_sd_raw_o) || (i_tx_phy_one_cnt == 3'h6))", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1', '17,1,0,0,1,1']}, '17,1,0,0,1,0': {'condition': "!(!(i_tx_phy_sd_raw_o) || (i_tx_phy_one_cnt == 3'h6))", 'action': "i_tx_phy_one_cnt <= (i_tx_phy_one_cnt + 3'h1);", 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1', '17,1,0,0,1,0']}}, {'18,0': {'condition': '', 'action': "i_tx_phy_stuff = (i_tx_phy_one_cnt == 3'h6);", 'block_path': ['18,0']}}, {'19,1': {'condition': '', 'action': '', 'block_path': ['19,1']}, '19,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_sd_bs_o <= 1'h0;", 'block_path': ['19,1', '19,1,1']}, '19,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['19,1', '19,1,0']}, '19,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_tx_phy_sd_bs_o <= ( ( !( i_tx_phy_tx_ip_sync) ) ? ( 1'b0 ) : ( ( ( ( i_tx_phy_one_cnt == 3'h6 ) ) ? ( 1'b0 ) : ( i_tx_phy_sd_raw_o ) ) ) );", 'block_path': ['19,1', '19,1,0', '19,1,0,1']}}, {'20,1': {'condition': '', 'action': '', 'block_path': ['20,1']}, '20,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_sd_nrzi_o <= 1'b1;", 'block_path': ['20,1', '20,1,1']}, '20,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['20,1', '20,1,0']}, '20,1,0,1': {'condition': '(!(i_tx_phy_tx_ip_sync) || !(i_tx_phy_txoe_r1))', 'action': "i_tx_phy_sd_nrzi_o <= 1'b1;", 'block_path': ['20,1', '20,1,0', '20,1,0,1']}, '20,1,0,0': {'condition': '!(!(i_tx_phy_tx_ip_sync) || !(i_tx_phy_txoe_r1))', 'action': '', 'block_path': ['20,1', '20,1,0', '20,1,0,0']}, '20,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_sd_nrzi_o <= ( ( i_tx_phy_sd_bs_o ) ? ( i_tx_phy_sd_nrzi_o ) : ( ~( i_tx_phy_sd_nrzi_o) ) );', 'block_path': ['20,1', '20,1,0', '20,1,0,0', '20,1,0,0,1']}}, {'21,1': {'condition': '', 'action': '', 'block_path': ['21,1']}, '21,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b0;", 'block_path': ['21,1', '21,1,1']}, '21,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['21,1', '21,1,0']}, '21,1,0,1': {'condition': "(i_tx_phy_ld_eop_d) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b1;", 'block_path': ['21,1', '21,1,0', '21,1,0,1']}, '21,1,0,0': {'condition': "!(i_tx_phy_ld_eop_d) == 1'b1", 'action': '', 'block_path': ['21,1', '21,1,0', '21,1,0,0']}, '21,1,0,0,1': {'condition': "(i_tx_phy_app_eop_sync2) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1']}}, {'22,1': {'condition': '', 'action': '', 'block_path': ['22,1']}, '22,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync1 <= 1'b0;", 'block_path': ['22,1', '22,1,1']}, '22,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['22,1', '22,1,0']}, '22,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync1 <= i_tx_phy_app_eop;', 'block_path': ['22,1', '22,1,0', '22,1,0,1']}}, {'23,1': {'condition': '', 'action': '', 'block_path': ['23,1']}, '23,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync2 <= 1'b0;", 'block_path': ['23,1', '23,1,1']}, '23,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['23,1', '23,1,0']}, '23,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync2 <= i_tx_phy_app_eop_sync1;', 'block_path': ['23,1', '23,1,0', '23,1,0,1']}}, {'24,1': {'condition': '', 'action': '', 'block_path': ['24,1']}, '24,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync3 <= 1'b0;", 'block_path': ['24,1', '24,1,1']}, '24,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['24,1', '24,1,0']}, '24,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync3 <= ( i_tx_phy_app_eop_sync2 | ( i_tx_phy_app_eop_sync3 & !( i_tx_phy_app_eop_sync4) ) );', 'block_path': ['24,1', '24,1,0', '24,1,0,1']}}, {'25,1': {'condition': '', 'action': '', 'block_path': ['25,1']}, '25,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync4 <= 1'b0;", 'block_path': ['25,1', '25,1,1']}, '25,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0']}, '25,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync4 <= i_tx_phy_app_eop_sync3;', 'block_path': ['25,1', '25,1,0', '25,1,0,1']}}, {'26,1': {'condition': '', 'action': '', 'block_path': ['26,1']}, '26,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe_r1 <= 1'b0;", 'block_path': ['26,1', '26,1,1']}, '26,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['26,1', '26,1,0']}, '26,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe_r1 <= i_tx_phy_tx_ip_sync;', 'block_path': ['26,1', '26,1,0', '26,1,0,1']}}, {'27,1': {'condition': '', 'action': '', 'block_path': ['27,1']}, '27,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe_r2 <= 1'b0;", 'block_path': ['27,1', '27,1,1']}, '27,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['27,1', '27,1,0']}, '27,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe_r2 <= i_tx_phy_txoe_r1;', 'block_path': ['27,1', '27,1,0', '27,1,0,1']}}, {'28,1': {'condition': '', 'action': '', 'block_path': ['28,1']}, '28,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe <= 1'b1;", 'block_path': ['28,1', '28,1,1']}, '28,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['28,1', '28,1,0']}, '28,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe <= !((i_tx_phy_txoe_r1 | i_tx_phy_txoe_r2));', 'block_path': ['28,1', '28,1,0', '28,1,0,1']}}, {'29,1': {'condition': '', 'action': '', 'block_path': ['29,1']}, '29,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txdp <= 1'b1;", 'block_path': ['29,1', '29,1,1']}, '29,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['29,1', '29,1,0']}, '29,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txdp <= ( ( phy_tx_mode ) ? ( ( !( i_tx_phy_app_eop_sync3) & i_tx_phy_sd_nrzi_o ) ) : ( i_tx_phy_sd_nrzi_o ) );', 'block_path': ['29,1', '29,1,0', '29,1,0,1']}}, {'30,1': {'condition': '', 'action': '', 'block_path': ['30,1']}, '30,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txdn <= 1'b0;", 'block_path': ['30,1', '30,1,1']}, '30,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['30,1', '30,1,0']}, '30,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txdn <= ( ( phy_tx_mode ) ? ( ( !( i_tx_phy_app_eop_sync3) & ~( i_tx_phy_sd_nrzi_o) ) ) : ( i_tx_phy_app_eop_sync3 ) );', 'block_path': ['30,1', '30,1,0', '30,1,0,1']}}, {'31,1': {'condition': '', 'action': '', 'block_path': ['31,1']}, '31,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_state <= 3'd0;", 'block_path': ['31,1', '31,1,1']}, '31,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_tx_phy_state <= i_tx_phy_next_state;', 'block_path': ['31,1', '31,1,0']}}, {'32,0': {'condition': '', 'action': "i_tx_phy_next_state = i_tx_phy_state;i_tx_phy_tx_ready_d = 1'b0;i_tx_phy_ld_sop_d = 1'b0;i_tx_phy_ld_data_d = 1'b0;i_tx_phy_ld_eop_d = 1'b0;", 'block_path': ['32,0']}, '32,0,1': {'condition': "(i_tx_phy_state) == 3'd0", 'action': '', 'block_path': ['32,0', '32,0,1']}, '32,0,1,1': {'condition': "(TxValid_i) == 1'b1", 'action': "i_tx_phy_ld_sop_d = 1'b1;i_tx_phy_next_state = 3'h1;", 'block_path': ['32,0', '32,0,1', '32,0,1,1']}, '32,0,2': {'condition': "(i_tx_phy_state) == 3'h1", 'action': '', 'block_path': ['32,0', '32,0,2']}, '32,0,2,1': {'condition': "(i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)) == 1'b1", 'action': "i_tx_phy_tx_ready_d = 1'b1;i_tx_phy_ld_data_d = 1'b1;i_tx_phy_next_state = 3'h2;", 'block_path': ['32,0', '32,0,2', '32,0,2,1']}, '32,0,3': {'condition': "(i_tx_phy_state) == 3'h2", 'action': '', 'block_path': ['32,0', '32,0,3']}, '32,0,3,1': {'condition': '(!(i_tx_phy_data_done) && (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)))', 'action': "i_tx_phy_ld_eop_d = 1'b1;i_tx_phy_next_state = 3'h3;", 'block_path': ['32,0', '32,0,3', '32,0,3,1']}, '32,0,3,1,1': {'condition': '(i_tx_phy_data_done && (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)))', 'action': "i_tx_phy_tx_ready_d = 1'b1;i_tx_phy_ld_data_d = 1'b1;", 'block_path': ['32,0', '32,0,3', '32,0,3,1', '32,0,3,1,1']}, '32,0,4': {'condition': "(i_tx_phy_state) == 3'h3", 'action': '', 'block_path': ['32,0', '32,0,4']}, '32,0,4,1': {'condition': "(i_tx_phy_app_eop_sync3) == 1'b1", 'action': "i_tx_phy_next_state = 3'h4;", 'block_path': ['32,0', '32,0,4', '32,0,4,1']}, '32,0,5': {'condition': "(i_tx_phy_state) == 3'h4", 'action': '', 'block_path': ['32,0', '32,0,5']}, '32,0,5,1': {'condition': '(!(i_tx_phy_app_eop_sync3) && i_rx_phy_fs_ce)', 'action': "i_tx_phy_next_state = 3'h5;", 'block_path': ['32,0', '32,0,5', '32,0,5,1']}, '32,0,6': {'condition': "(i_tx_phy_state) == 3'h5", 'action': '', 'block_path': ['32,0', '32,0,6']}, '32,0,6,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_tx_phy_next_state = 3'd0;", 'block_path': ['32,0', '32,0,6', '32,0,6,1']}}, {'33,0': {'condition': '', 'action': 'DataIn_o = i_rx_phy_hold_reg;', 'block_path': ['33,0']}}, {'34,0': {'condition': '', 'action': 'RxValid_o = i_rx_phy_rx_valid;', 'block_path': ['34,0']}}, {'35,0': {'condition': '', 'action': 'RxActive_o = i_rx_phy_rx_active;', 'block_path': ['35,0']}}, {'36,0': {'condition': '', 'action': 'RxError_o = ((i_rx_phy_sync_err | i_rx_phy_bit_stuff_err) | i_rx_phy_byte_err);', 'block_path': ['36,0']}}, {'37,0': {'condition': '', 'action': 'LineState_o = {i_rx_phy_rxdn_s1, i_rx_phy_rxdp_s1};', 'block_path': ['37,0']}}, {'38,1': {'condition': '', 'action': 'i_rx_phy_rx_en <= txoe;', 'block_path': ['38,1']}}, {'39,1': {'condition': '', 'action': 'i_rx_phy_sync_err <= (!(i_rx_phy_rx_active) & i_rx_phy_sync_err_d);', 'block_path': ['39,1']}}, {'40,1': {'condition': '', 'action': 'i_rx_phy_rxd_s0 <= rxd;', 'block_path': ['40,1']}}, {'41,1': {'condition': '', 'action': 'i_rx_phy_rxd_s1 <= i_rx_phy_rxd_s0;', 'block_path': ['41,1']}}, {'42,1': {'condition': '', 'action': '', 'block_path': ['42,1']}, '42,1,1': {'condition': '(i_rx_phy_rxd_s0 && i_rx_phy_rxd_s1)', 'action': "i_rx_phy_rxd_s <= 1'b1;", 'block_path': ['42,1', '42,1,1']}, '42,1,0': {'condition': '!(i_rx_phy_rxd_s0 && i_rx_phy_rxd_s1)', 'action': '', 'block_path': ['42,1', '42,1,0']}, '42,1,0,1': {'condition': '(!(i_rx_phy_rxd_s0) && !(i_rx_phy_rxd_s1))', 'action': "i_rx_phy_rxd_s <= 1'b0;", 'block_path': ['42,1', '42,1,0', '42,1,0,1']}}, {'43,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s0 <= rxdp;', 'block_path': ['43,1']}}, {'44,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s1 <= i_rx_phy_rxdp_s0;', 'block_path': ['44,1']}}, {'45,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s_r <= (i_rx_phy_rxdp_s0 & i_rx_phy_rxdp_s1);', 'block_path': ['45,1']}}, {'46,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s <= ((i_rx_phy_rxdp_s0 & i_rx_phy_rxdp_s1) | i_rx_phy_rxdp_s_r);', 'block_path': ['46,1']}}, {'47,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s0 <= rxdn;', 'block_path': ['47,1']}}, {'48,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s1 <= i_rx_phy_rxdn_s0;', 'block_path': ['48,1']}}, {'49,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s_r <= (i_rx_phy_rxdn_s0 & i_rx_phy_rxdn_s1);', 'block_path': ['49,1']}}, {'50,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s <= ((i_rx_phy_rxdn_s0 & i_rx_phy_rxdn_s1) | i_rx_phy_rxdn_s_r);', 'block_path': ['50,1']}}, {'51,1': {'condition': '', 'action': '', 'block_path': ['51,1']}, '51,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_se0_s <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s));', 'block_path': ['51,1', '51,1,1']}}, {'52,1': {'condition': '', 'action': 'i_rx_phy_rxd_r <= i_rx_phy_rxd_s;', 'block_path': ['52,1']}}, {'53,1': {'condition': '', 'action': '', 'block_path': ['53,1']}, '53,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_dpll_state <= 2'h1;", 'block_path': ['53,1', '53,1,1']}, '53,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_rx_phy_dpll_state <= i_rx_phy_dpll_next_state;', 'block_path': ['53,1', '53,1,0']}}, {'54,0': {'condition': '', 'action': "i_rx_phy_fs_ce_d = 1'b0;", 'block_path': ['54,0']}, '54,0,1': {'condition': "(i_rx_phy_dpll_state) == 2'h0", 'action': '', 'block_path': ['54,0', '54,0,1']}, '54,0,1,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,1', '54,0,1,1']}, '54,0,1,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h1;", 'block_path': ['54,0', '54,0,1', '54,0,1,0']}, '54,0,2': {'condition': "(i_rx_phy_dpll_state) == 2'h1", 'action': "i_rx_phy_fs_ce_d = 1'b1;", 'block_path': ['54,0', '54,0,2']}, '54,0,2,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h3;", 'block_path': ['54,0', '54,0,2', '54,0,2,1']}, '54,0,2,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h2;", 'block_path': ['54,0', '54,0,2', '54,0,2,0']}, '54,0,3': {'condition': "(i_rx_phy_dpll_state) == 2'h2", 'action': '', 'block_path': ['54,0', '54,0,3']}, '54,0,3,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,3', '54,0,3,1']}, '54,0,3,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h3;", 'block_path': ['54,0', '54,0,3', '54,0,3,0']}, '54,0,4': {'condition': "(i_rx_phy_dpll_state) == 2'h3", 'action': '', 'block_path': ['54,0', '54,0,4']}, '54,0,4,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,4', '54,0,4,1']}, '54,0,4,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,4', '54,0,4,0']}}, {'55,1': {'condition': '', 'action': 'i_rx_phy_fs_ce_r1 <= i_rx_phy_fs_ce_d;', 'block_path': ['55,1']}}, {'56,1': {'condition': '', 'action': 'i_rx_phy_fs_ce_r2 <= i_rx_phy_fs_ce_r1;', 'block_path': ['56,1']}}, {'57,1': {'condition': '', 'action': 'i_rx_phy_fs_ce <= i_rx_phy_fs_ce_r2;', 'block_path': ['57,1']}}, {'58,1': {'condition': '', 'action': '', 'block_path': ['58,1']}, '58,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_fs_state <= 3'h0;", 'block_path': ['58,1', '58,1,1']}, '58,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_rx_phy_fs_state <= i_rx_phy_fs_next_state;', 'block_path': ['58,1', '58,1,0']}}, {'59,0': {'condition': '', 'action': "i_rx_phy_synced_d = 1'b0;i_rx_phy_sync_err_d = 1'b0;i_rx_phy_fs_next_state = i_rx_phy_fs_state;", 'block_path': ['59,0']}, '59,0,1': {'condition': '( ( ( i_rx_phy_fs_ce && !( i_rx_phy_rx_active) ) && !( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) )) ) && !( i_rx_phy_se0_s) )', 'action': '', 'block_path': ['59,0', '59,0,1']}, '59,0,1,1': {'condition': "(i_rx_phy_fs_state) == 3'h0", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,1']}, '59,0,1,1,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h1;", 'block_path': ['59,0', '59,0,1', '59,0,1,1', '59,0,1,1,1']}, '59,0,1,2': {'condition': "(i_rx_phy_fs_state) == 3'h1", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,2']}, '59,0,1,2,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h2;", 'block_path': ['59,0', '59,0,1', '59,0,1,2', '59,0,1,2,1']}, '59,0,1,2,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,2', '59,0,1,2,0']}, '59,0,1,3': {'condition': "(i_rx_phy_fs_state) == 3'h2", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,3']}, '59,0,1,3,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h3;", 'block_path': ['59,0', '59,0,1', '59,0,1,3', '59,0,1,3,1']}, '59,0,1,3,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,3', '59,0,1,3,0']}, '59,0,1,4': {'condition': "(i_rx_phy_fs_state) == 3'h3", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,4']}, '59,0,1,4,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h4;", 'block_path': ['59,0', '59,0,1', '59,0,1,4', '59,0,1,4,1']}, '59,0,1,4,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,4', '59,0,1,4,0']}, '59,0,1,5': {'condition': "(i_rx_phy_fs_state) == 3'h4", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,5']}, '59,0,1,5,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h5;", 'block_path': ['59,0', '59,0,1', '59,0,1,5', '59,0,1,5,1']}, '59,0,1,5,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,5', '59,0,1,5,0']}, '59,0,1,6': {'condition': "(i_rx_phy_fs_state) == 3'h5", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,6']}, '59,0,1,6,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h6;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,1']}, '59,0,1,6,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0']}, '59,0,1,6,0,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h0;i_rx_phy_synced_d = 1'b1;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0', '59,0,1,6,0,1']}, '59,0,1,6,0,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0', '59,0,1,6,0,0']}, '59,0,1,7': {'condition': "(i_rx_phy_fs_state) == 3'h6", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,7']}, '59,0,1,7,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h7;", 'block_path': ['59,0', '59,0,1', '59,0,1,7', '59,0,1,7,1']}, '59,0,1,7,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,7', '59,0,1,7,0']}, '59,0,1,8': {'condition': "(i_rx_phy_fs_state) == 3'h7", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,8']}, '59,0,1,8,1': {'condition': "(!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) == 1'b1", 'action': "i_rx_phy_synced_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,8', '59,0,1,8,1']}}, {'60,1': {'condition': '', 'action': '', 'block_path': ['60,1']}, '60,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_rx_active <= 1'b0;", 'block_path': ['60,1', '60,1,1']}, '60,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['60,1', '60,1,0']}, '60,1,0,1': {'condition': '(i_rx_phy_synced_d && i_rx_phy_rx_en)', 'action': "i_rx_phy_rx_active <= 1'b1;", 'block_path': ['60,1', '60,1,0', '60,1,0,1']}, '60,1,0,0': {'condition': '!(i_rx_phy_synced_d && i_rx_phy_rx_en)', 'action': '', 'block_path': ['60,1', '60,1,0', '60,1,0,0']}, '60,1,0,0,1': {'condition': '((!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_valid_r)', 'action': "i_rx_phy_rx_active <= 1'b0;", 'block_path': ['60,1', '60,1,0', '60,1,0,0', '60,1,0,0,1']}}, {'61,1': {'condition': '', 'action': '', 'block_path': ['61,1']}, '61,1,1': {'condition': "(i_rx_phy_rx_valid) == 1'b1", 'action': "i_rx_phy_rx_valid_r <= 1'b1;", 'block_path': ['61,1', '61,1,1']}, '61,1,0': {'condition': "!(i_rx_phy_rx_valid) == 1'b1", 'action': '', 'block_path': ['61,1', '61,1,0']}, '61,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_rx_phy_rx_valid_r <= 1'b0;", 'block_path': ['61,1', '61,1,0', '61,1,0,1']}}, {'62,1': {'condition': '', 'action': '', 'block_path': ['62,1']}, '62,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_sd_r <= i_rx_phy_rxd_s;', 'block_path': ['62,1', '62,1,1']}}, {'63,1': {'condition': '', 'action': '', 'block_path': ['63,1']}, '63,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_sd_nrzi <= 1'b0;", 'block_path': ['63,1', '63,1,1']}, '63,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['63,1', '63,1,0']}, '63,1,0,1': {'condition': "(!(i_rx_phy_rx_active)) == 1'b1", 'action': "i_rx_phy_sd_nrzi <= 1'b1;", 'block_path': ['63,1', '63,1,0', '63,1,0,1']}, '63,1,0,0': {'condition': "!(!(i_rx_phy_rx_active)) == 1'b1", 'action': '', 'block_path': ['63,1', '63,1,0', '63,1,0,0']}, '63,1,0,0,1': {'condition': '(i_rx_phy_rx_active && i_rx_phy_fs_ce)', 'action': 'i_rx_phy_sd_nrzi <= !((i_rx_phy_rxd_s ^ i_rx_phy_sd_r));', 'block_path': ['63,1', '63,1,0', '63,1,0,0', '63,1,0,0,1']}}, {'64,1': {'condition': '', 'action': '', 'block_path': ['64,1']}, '64,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,1']}, '64,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0']}, '64,1,0,1': {'condition': "(!(i_rx_phy_shift_en)) == 1'b1", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,0', '64,1,0,1']}, '64,1,0,0': {'condition': "!(!(i_rx_phy_shift_en)) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0', '64,1,0,0']}, '64,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1']}, '64,1,0,0,1,1': {'condition': "(!(i_rx_phy_sd_nrzi) || (i_rx_phy_one_cnt == 3'h6))", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1', '64,1,0,0,1,1']}, '64,1,0,0,1,0': {'condition': "!(!(i_rx_phy_sd_nrzi) || (i_rx_phy_one_cnt == 3'h6))", 'action': "i_rx_phy_one_cnt <= (i_rx_phy_one_cnt + 3'h1);", 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1', '64,1,0,0,1,0']}}, {'65,1': {'condition': '', 'action': "i_rx_phy_bit_stuff_err <= ( ( ( ( ( i_rx_phy_one_cnt == 3'h6 ) & i_rx_phy_sd_nrzi ) & i_rx_phy_fs_ce ) & !( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) )) ) & i_rx_phy_rx_active );", 'block_path': ['65,1']}}, {'66,1': {'condition': '', 'action': '', 'block_path': ['66,1']}, '66,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_shift_en <= (i_rx_phy_synced_d | i_rx_phy_rx_active);', 'block_path': ['66,1', '66,1,1']}}, {'67,1': {'condition': '', 'action': '', 'block_path': ['67,1']}, '67,1,1': {'condition': "((i_rx_phy_fs_ce && i_rx_phy_shift_en) && !((i_rx_phy_one_cnt == 3'h6)))", 'action': 'i_rx_phy_hold_reg <= {i_rx_phy_sd_nrzi, i_rx_phy_hold_reg[7:1]};', 'block_path': ['67,1', '67,1,1']}}, {'68,1': {'condition': '', 'action': '', 'block_path': ['68,1']}, '68,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_bit_cnt <= 3'b0;", 'block_path': ['68,1', '68,1,1']}, '68,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['68,1', '68,1,0']}, '68,1,0,1': {'condition': "(!(i_rx_phy_shift_en)) == 1'b1", 'action': "i_rx_phy_bit_cnt <= 3'h0;", 'block_path': ['68,1', '68,1,0', '68,1,0,1']}, '68,1,0,0': {'condition': "!(!(i_rx_phy_shift_en)) == 1'b1", 'action': '', 'block_path': ['68,1', '68,1,0', '68,1,0,0']}, '68,1,0,0,1': {'condition': "(i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6)))", 'action': "i_rx_phy_bit_cnt <= (i_rx_phy_bit_cnt + 3'h1);", 'block_path': ['68,1', '68,1,0', '68,1,0,0', '68,1,0,0,1']}}, {'69,1': {'condition': '', 'action': '', 'block_path': ['69,1']}, '69,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_rx_valid1 <= 1'b0;", 'block_path': ['69,1', '69,1,1']}, '69,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['69,1', '69,1,0']}, '69,1,0,1': {'condition': "((i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6))) && (i_rx_phy_bit_cnt == 3'h7))", 'action': "i_rx_phy_rx_valid1 <= 1'b1;", 'block_path': ['69,1', '69,1,0', '69,1,0,1']}, '69,1,0,0': {'condition': "!((i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6))) && (i_rx_phy_bit_cnt == 3'h7))", 'action': '', 'block_path': ['69,1', '69,1,0', '69,1,0,0']}, '69,1,0,0,1': {'condition': "((i_rx_phy_rx_valid1 && i_rx_phy_fs_ce) && !((i_rx_phy_one_cnt == 3'h6)))", 'action': "i_rx_phy_rx_valid1 <= 1'b0;", 'block_path': ['69,1', '69,1,0', '69,1,0,0', '69,1,0,0,1']}}, {'70,1': {'condition': '', 'action': "i_rx_phy_rx_valid <= ((!((i_rx_phy_one_cnt == 3'h6)) & i_rx_phy_rx_valid1) & i_rx_phy_fs_ce);", 'block_path': ['70,1']}}, {'71,1': {'condition': '', 'action': 'i_rx_phy_se0_r <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s));', 'block_path': ['71,1']}}, {'72,1': {'condition': '', 'action': 'i_rx_phy_byte_err <= ( ( ( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) ) & !( i_rx_phy_se0_r) ) & |( i_rx_phy_bit_cnt[2:1]) ) & i_rx_phy_rx_active );', 'block_path': ['72,1']}}]

    CDFG_list = [{'0,0': {'condition': '', 'action': '', 'block_path': ['0,0']}, '0,0,1': {'condition': "(rst == 1'b1)", 'action': "State0 <= 1'b0;State1 <= 1'b0;State2 <= 1'b0;State3 <= 1'b0;", 'block_path': ['0,0', '0,0,1']}, '0,0,0': {'condition': "!(rst == 1'b1)", 'action': '', 'block_path': ['0,0', '0,0,0']}, '0,0,0,1': {'condition': "(state == 128'h3243f6a8_885a308d_313198a2_e0370734)", 'action': "State0 <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,1']}, '0,0,0,0': {'condition': "!(state == 128'h3243f6a8_885a308d_313198a2_e0370734)", 'action': '', 'block_path': ['0,0', '0,0,0', '0,0,0,0']}, '0,0,0,0,1': {'condition': "((state == 128'h00112233_44556677_8899aabb_ccddeeff) && (State0 == 1'b1))", 'action': "State1 <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,1']}, '0,0,0,0,0': {'condition': "!((state == 128'h00112233_44556677_8899aabb_ccddeeff) && (State0 == 1'b1))", 'action': '', 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,0']}, '0,0,0,0,0,1': {'condition': "((state == 128'h0) && (State1 == 1'b1))", 'action': "State2 <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,0', '0,0,0,0,0,1']}, '0,0,0,0,0,0': {'condition': "!((state == 128'h0) && (State1 == 1'b1))", 'action': '', 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,0', '0,0,0,0,0,0']}, '0,0,0,0,0,0,1': {'condition': "((state == 128'h1) && (State2 == 1'b1))", 'action': "State3 <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,0', '0,0,0,0,0,0', '0,0,0,0,0,0,1']}}, {'1,0': {'condition': '', 'action': 'Tj_Trig <= State0 & State1 & State2 & State3;', 'block_path': ['1,0']}}, {'2,0': {'condition': '', 'action': 'data = state;', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': 'lfsr = lfsr_stream;', 'block_path': ['3,0']}}, {'4,0': {'condition': '', 'action': 'd0 = lfsr_stream[15] ^ lfsr_stream[11] ^ lfsr_stream[7] ^ lfsr_stream[0];', 'block_path': ['4,0']}}, {'5,1': {'condition': '', 'action': '', 'block_path': ['5,1']}, '5,1,1': {'condition': "(rst == 1'b1)", 'action': 'lfsr_stream <= data[19:0];', 'block_path': ['5,1', '5,1,1']}, '5,1,0': {'condition': "!(rst == 1'b1)", 'action': '', 'block_path': ['5,1', '5,1,0']}, '5,1,0,1': {'condition': "(Tj_Trig == 1'b1)", 'action': 'lfsr_stream <= {d0, lfsr_stream[19:1]};', 'block_path': ['5,1', '5,1,0', '5,1,0,1']}, '5,1,0,0': {'condition': "!(Tj_Trig == 1'b1)", 'action': 'lfsr_stream <= lfsr_stream;', 'block_path': ['5,1', '5,1,0', '5,1,0,0']}}, {'6,0': {'condition': '', 'action': 'counter = lfsr_stream;', 'block_path': ['6,0']}}, {'7,0': {'condition': '', 'action': 'Capacitance = load;', 'block_path': ['7,0']}}, {'8,1': {'condition': '', 'action': 'load[0] <= key[0] ^ counter[0];load[1] <= key[0] ^ counter[0];load[2] <= key[0] ^ counter[0];load[3] <= key[0] ^ counter[0];load[4] <= key[0] ^ counter[0];load[5] <= key[0] ^ counter[0];load[6] <= key[0] ^ counter[0];load[7] <= key[0] ^ counter[0];load[8] <= key[1] ^ counter[1];load[9] <= key[1] ^ counter[1];load[10] <= key[1] ^ counter[1];load[11] <= key[1] ^ counter[1];load[12] <= key[1] ^ counter[1];load[13] <= key[1] ^ counter[1];load[14] <= key[1] ^ counter[1];load[15] <= key[1] ^ counter[1];load[16] <= key[2] ^ counter[2];load[17] <= key[2] ^ counter[2];load[18] <= key[2] ^ counter[2];load[19] <= key[2] ^ counter[2];load[20] <= key[2] ^ counter[2];load[21] <= key[2] ^ counter[2];load[22] <= key[2] ^ counter[2];load[23] <= key[2] ^ counter[2];load[24] <= key[3] ^ counter[3];load[25] <= key[3] ^ counter[3];load[26] <= key[3] ^ counter[3];load[27] <= key[3] ^ counter[3];load[28] <= key[3] ^ counter[3];load[29] <= key[3] ^ counter[3];load[30] <= key[3] ^ counter[3];load[31] <= key[3] ^ counter[3];load[32] <= key[4] ^ counter[4];load[33] <= key[4] ^ counter[4];load[34] <= key[4] ^ counter[4];load[35] <= key[4] ^ counter[4];load[36] <= key[4] ^ counter[4];load[37] <= key[4] ^ counter[4];load[38] <= key[4] ^ counter[4];load[39] <= key[4] ^ counter[4];load[40] <= key[5] ^ counter[5];load[41] <= key[5] ^ counter[5];load[42] <= key[5] ^ counter[5];load[43] <= key[5] ^ counter[5];load[44] <= key[5] ^ counter[5];load[45] <= key[5] ^ counter[5];load[46] <= key[5] ^ counter[5];load[47] <= key[5] ^ counter[5];load[48] <= key[6] ^ counter[6];load[49] <= key[6] ^ counter[6];load[50] <= key[6] ^ counter[6];load[51] <= key[6] ^ counter[6];load[52] <= key[6] ^ counter[6];load[53] <= key[6] ^ counter[6];load[54] <= key[6] ^ counter[6];load[55] <= key[6] ^ counter[6];load[56] <= key[7] ^ counter[7];load[57] <= key[7] ^ counter[7];load[58] <= key[7] ^ counter[7];load[59] <= key[7] ^ counter[7];load[60] <= key[7] ^ counter[7];load[61] <= key[7] ^ counter[7];load[62] <= key[7] ^ counter[7];load[63] <= key[7] ^ counter[7];', 'block_path': ['8,1']}}]

    main()
