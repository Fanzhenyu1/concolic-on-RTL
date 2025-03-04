from math import *
import re
import os, glob
import sys
import random
import copy
import subprocess
import CDFG_1_1
from z3 import *
import verilog2z3
import time
import psutil
import gc
from threading import Thread, Event
# result_CDFG = subprocess.run(['python', 'd:\mylife_yanjiu\project\RTL-Contest\CDFG_1.py'], stdout=subprocess.PIPE)
# rtl_CDFG = result_CDFG.stdout.decode('utf-8')

# 监控模块
class MemoryMonitor(Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = Event()
        self.peak_memory = 0  # 单位：KB
        self.process = psutil.Process(os.getpid())
        self.ready_event = Event()  # 新增准备就绪信号

    def _get_current_memory(self):
        """获取当前进程内存使用量"""
        return self.process.memory_info().rss / 1024  # 转换为KB

    def run(self):
        """持续监控内存使用情况"""
        # 在监控开始时获取初始内存
        initial_memory = self._get_current_memory()
        self.ready_event.set()  # 发出准备就绪信号
        
        while not self.stop_event.wait(timeout=0.001):  # 采样间隔提升到1ms
            current_mem = self._get_current_memory() - initial_memory
            if current_mem > self.peak_memory:
                self.peak_memory = current_mem

    def stop(self):
        """停止监控线程"""
        self.stop_event.set()
        self.join(timeout=1)

def not_empty(s):
    return s and s.strip()

def inout_extract(dict_block, reset_name):                  # 提取条件与操作中的输入输出信号，便于路径生成
    constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量
    signal_pattern = r'(?<!\')\b[a-zA-Z_]\w*\b'             # 匹配信号，但排除以单引号开头的数字常量
    for key, value in dict_block.items():       # value为字典，含有条件、操作、块内路径信息
        str_condition = value['condition']
        str_action = value['action']
        action_list = str_action.split(';')
        action_list = list(filter(not_empty, action_list))
        ##确定分隔符##
        list_condition = re.split(r"[!&()*+<=>| \-]+", str_condition)
        pass
        list_condition = list(filter(not_empty, list_condition))
        ## 删去条件中的常量项 ##
        for i in range(len(list_condition)):
            if re.match(constant_pattern, list_condition[i]) or list_condition[i] == reset_name:
                list_condition[i] = ''
        list_condition = list(filter(not_empty, list_condition))

        action_in = []
        action_out = []
        if str_action != '':
            for action_one in action_list:
                action_out.append(action_one.strip().split(' ')[0])
                action_instr = action_one.split('=')[1]
                # action_inlist = re.split(r"[!&()*+| \-]+", action_instr)
                action_inlist = re.findall(signal_pattern, action_instr)
                action_inlist = list(filter(not_empty, action_inlist))
                for item in action_inlist:
                    action_in.append(item)
        else:
            action_in = []
            action_out = []
        ## 删去操作中的常量项 ##
        for i in range(len(action_in)):
            if re.match(constant_pattern, action_in[i]):
                action_in[i] = ''
        action_in = list(filter(not_empty, action_in))
        for i in range(len(action_out)):
            if re.match(constant_pattern, action_out[i]):
                action_out[i] = ''
        action_out = list(filter(not_empty, action_out))
        
        value['action_in'] = action_in
        value['action_out'] = action_out
        value['condition_in'] = list_condition
        
        pass
    pass
    return dict_block

def path_generate(dict_CDFG_inout, target_node_list, reset_name):
    target_path_C = []
    target_path_D = []
    target_path_all = []
    if target_node_list == []:
        print('路径生成结束')
        return 0
    else:
        target_node = target_node_list[-1]            # 取出一个目标节点，栈顶
        target_node_list.pop()                        # 栈顶元素出栈
        path_in_block = dict_CDFG_inout[target_node]['block_path']
    path_list_C = []
    path_list_D = []

    dict_target_node = dict_CDFG_inout[target_node]      # 目标节点信息
    node_action_in = dict_target_node['action_in']
    # node_action_out = dict_target_node['action_out']
    # node_condition_in = dict_target_node['condition_in']

    ############## 构造控制依赖信号列表 ########
    ctr_dep_list = []
    for node in path_in_block:
        if reset_name not in dict_CDFG_inout[node]['condition']:  # 排除reset信号
            ctr_dep_list.extend(dict_CDFG_inout[node]['condition_in'])
    ctr_dep_list = list(set(ctr_dep_list))
    pass
    print(f"目标节点'{target_node}'控制依赖信号列表：{ctr_dep_list}")
    print(f"目标节点'{target_node}'数据依赖信号列表：{node_action_in}")
    ############## 控制依赖路径搭建#############
    for key, value in dict_CDFG_inout.items():           # 遍历所有节点
        sub_node_action_out = dict_CDFG_inout[key]['action_out']    # 提取可能上一级节点的输出信号
        path_list_C.append(target_node)                    # 开始构建目标路径
        sub_node_true = 0
        for i in ctr_dep_list:
            if i.split('[')[0] in sub_node_action_out:      #@1111
                if reset_name not in dict_CDFG_inout[key]['condition']:
                    sub_node_true = 1
        if sub_node_true == 1:
            target_node_list.append(key)          # 寻找上一级节点并将目标节点入栈
            path_list_C.append(key)                 # 构建目标路径上级节点
            path_list_C.append('1')                 # 构建目标路径控制流路径信息
            if target_node.split(",")[1] == '1' and key.split(",")[1] == '1':
                path_list_C.append('1')             # 构建目标路径时序参数 时->时
            elif target_node.split(",")[1] == '0' and key.split(",")[1] == '0':
                path_list_C.append('0')             # 构建目标路径时序参数 组->组
            elif target_node.split(",")[1] == '0' and key.split(",")[1] == '1':
                path_list_C.append('0')             # 构建目标路径时序参数 组->时                
            else:
                path_list_C.append('1')             # 构建目标路径时序参数 时->组
            target_path_C.append(path_list_C)
        pass
        path_list_C = []

    ############## 数据依赖路径搭建#############
    for key, value in dict_CDFG_inout.items():           # 遍历所有节点
        sub_node_action_out = dict_CDFG_inout[key]['action_out']    # 提取可能上一级节点的输出信号
        path_list_D.append(target_node)                    # 开始构建目标路径
        for i in node_action_in:
            if i.split('[')[0] in sub_node_action_out:
                target_node_list.append(key)          # 寻找上一级节点并将目标节点入栈
                path_list_D.append(key)                 # 构建目标路径上级节点
                path_list_D.append('0')                 # 构建目标路径数据流路径信息
                if target_node.split(",")[1] == '1' and key.split(",")[1] == '1':
                    path_list_D.append('1')
                elif target_node.split(",")[1] == '0' and key.split(",")[1] == '0':
                    path_list_D.append('0')
                elif target_node.split(",")[1] == '0' and key.split(",")[1] == '1':
                    path_list_D.append('0')
                else:
                    path_list_D.append('1')             # 构建目标路径时序参数
                target_path_D.append(path_list_D)
        path_list_D = []
    target_path_all = target_path_C + target_path_D
    print("所有路径：",target_path_all)
    pass
    return target_path_C,target_path_D

def path_search(dict_CDFG_inout, target_path_l, reset_name):
    # 全局变量
    global num_all
    global num_apt
    global path_list
    global constraint_stack
    global flag
    global num_start

    # 路径搜索
    for i in range(len(target_path_l)):
        # 建立初始约束
        constraint_stack = []        
        target_path = target_path_l[i]
        print(f"...当前路径{i+1}：{target_path}")
        pass
        # 确定当前路径下的上级节点
        target_node_up = target_path[1]
        # 建立当前路径下的约束
        if target_path[2] == '1':  # 控制流路径
            # constraint_condition = []
            block_path = dict_CDFG_inout[target_path[0]]['block_path']
            flag_rst = 0
            for m in range(len(block_path)):
                if reset_name not in dict_CDFG_inout[block_path[m]]['condition']:  # 排除reset信号
                    constraint_stack.append(dict_CDFG_inout[block_path[m]]['condition'])
                    print(f"添加控制流条件约束：{dict_CDFG_inout[block_path[m]]['condition']}")
                    flag_rst += 1
            if flag_rst == 0:
                print(f"warning: 路径{target_path}只包含reset相关")     # 一般不会触发
        else:  # 数据流路径
            # constraint_action = []
            constraint_stack.append(dict_CDFG_inout[target_path[0]]['action'])
            print(f"添加数据流操作约束：{dict_CDFG_inout[target_path[0]]['action']}")
        constraint_stack = list(filter(not_empty, constraint_stack))
        constraint_stack.append(dict_CDFG_inout[target_node_up]['action'])        # 加入上级节点的操作约束
        print(f"当前路径约束栈：{constraint_stack}")
        constraint_stack_1 = constraint_stack.copy()
        # 进行路径约束求解
        solver = Solver()
        signal_list, constraints = verilog2z3.verilog_to_z3(constraint_stack_1,[],[])
        pass
        for constraint in constraints:
            solver.add(eval(constraint))    
        if solver.check() == sat:
            print(f"当前路径约束下有解")
            num_apt += 1
            num_all += 1
            target_path.append(num_start)
            num_start += 1            
            path_list.append(target_path)
            # 进行依赖搜寻,获取上级路径列表
            pc,pd = path_generate(dict_CDFG_inout, [target_node_up], reset_name)
            target_path_up = pc + pd
            if target_path_up == []:
                num_start -= 1
            pass
            search_p(dict_CDFG_inout, target_path_up, reset_name)
        else:
            print(f"当前路径约束下无解,该路径跳过")
            num_all += 1
    pass
    return 0

def search_p(dict_CDFG_inout, path_l, reset_name):
    # 全局变量
    global num_all
    global num_apt
    global path_list
    global flag
    global constraint_stack
    global num_start
    # 正常变量
    flag_1 = 0
    for i in range(len(path_l)):

        target_path = path_l[i]
        print(f"...当前路径：{target_path}")
        pass
        
        if target_path[2] == '0':  # 数据流路径
            # 先加入上级节点的操作约束
            constraint_stack.append(dict_CDFG_inout[target_path[1]]['action'])
            # 直接求解约束
            print(f"当前路径约束栈：{constraint_stack}")
            constraint_stack_1 = constraint_stack.copy()
            # 进行路径约束求解
            solver = Solver()
            signal_list, constraints = verilog2z3.verilog_to_z3(constraint_stack_1,[],[])
            pass
            for constraint in constraints:
                solver.add(eval(constraint))    
            if solver.check() == sat:
                print(f"当前路径约束下有解")
                num_apt += 1
                num_all += 1         
                target_path.append(num_start)
                num_start += 1                     
                path_list.append(target_path)

                flag += 1
                pc,pd = path_generate(dict_CDFG_inout, [target_path[1]], reset_name)
                path_2 = pc + pd
                pass
                if path_2 == []:
                    num_start -= 1
                pass
                search_p(dict_CDFG_inout, path_2, reset_name)
            else:
                print(f"当前路径约束下无解,该路径跳过")
                num_all += 1
                constraint_stack = constraint_stack[:-1]  # 回溯
                continue
            continue      
        else:  # 控制流路径
            flag_1 += 1
            if flag > 0:
                constraint_stack = constraint_stack[:-1]  # 回溯
                num_start -= 1
                flag = 0
            pass
            continue
    if flag_1 == len(path_l) and flag_1 != 0:
        num_start -= 1
    return 0

def period_unify(path_list, now_node):    # 路径时序约束统一化
    # 添加初始优先级参数
    global num_start
    up_node = []
    flag_error = 0
    for i in range(len(path_list)):
        if path_list[i][0] == now_node:
            path_list[i].append(num_start)
            up_node.append(path_list[i][1])
            flag_error += 1
        else:
            continue
    if flag_error == 0:
        return 0

    for i in range(len(path_list)):
            if path_list[i][0] == up_node:
                pass
    pass
    num_start += 1
    return 0

def CDFG_inout_generate(list_CDFG, reset_name):
    # 节点信息补充，输入输出信号提取
    list_CDFG_inout = []
    for i in range(len(list_CDFG)):                # 遍历列表元素，数据类型为字典，含有一个块内的所有节点信息
        list_CDFG_inout.append(inout_extract(list_CDFG[i], reset_name))
        pass
    pass
    # print(list_CDFG_inout)
    dict_CDFG_inout = {}                           # 合并字典
    for i in list_CDFG_inout:
        dict_CDFG_inout.update(i)
        pass
    # print(dict_CDFG_inout)                        # 输出模块所有节点信息
    # print(list_inout)                             # 输出模块所有输入输出信号列表
    return dict_CDFG_inout

def main_1(target_node_list, dict_CDFG_inout):

    # 全局变量
    global num_all
    global num_apt
    global num_start
    global path_list
    global constraint_stack
    global flag
    global reset_name

    for i in range(len(target_node_list)):
        num_start = target_node_list[i][1]
        constraint_stack = []
        flag = 0

        path_in_block = dict_CDFG_inout[target_node]['block_path']
        print(f"目标节点块内路径：{path_in_block}")
        target_path_C,target_path_D = path_generate(dict_CDFG_inout, [target_node_list[i][0]], reset_name)         # 带递归
        print("目标节点控制依赖：",target_path_C)
        print("目标节点数据依赖：",target_path_D)
        pass
        target_path = target_path_C + target_path_D
        # print("所有路径：",target_path)

        # 路径搜索
        path_search(dict_CDFG_inout, target_path, reset_name)

        # 输出路径搜索结果
        print(f"路径约减结果：{num_apt}/{num_all}")
        print(f"路径搜索结果：{path_list}")

    return path_list

def main():
    # 全局变量
    global num_all
    global num_apt
    global path_list
    global constraint_stack
    global flag
    global reset_name
    global node_selected
    # 加强版垃圾回收
    for _ in range(3):
        gc.collect()
    monitor = MemoryMonitor()
    monitor.start()
    monitor.ready_event.wait()

    start_time = time.time()    

    # 输入输出信号提取
    dict_CDFG_inout = CDFG_inout_generate(list_CDFG, reset_name)
    # 目标节点入栈
    target_node_list = []
    target_node_list.append([target_node, num_start])             # 定义目标节点堆栈，第一个目标节点入栈
    node_selected.append(target_node)
    for i in range(4):
        path_list = main_1(target_node_list, dict_CDFG_inout)
        print(f"第{i+1}次搜索结果：{path_list}")
        target_node_list = []
        for j in range(len(path_list)):
            if path_list[j][2] == '1':                 # 定位控制流末端
                if path_list[j][1] not in node_selected:
                    target_node_list.append([path_list[j][1],path_list[j][4]])  # [上级节点，距离]
                    node_selected.append(path_list[j][1])
        pass
    pass

    monitor.stop()
    # monitor.join()
    end_time = time.time()
    execution_time = end_time - start_time
    gc.collect()
    print("Execution time in seconds: ", execution_time)
    print(f"峰值内存占用：{monitor.peak_memory:.2f} KB")
    return path_list
    

list_CDFG = [{'0,0,1': {'condition': "(int_state != 4'b0001) | (csr_state != 5'b00001)", 'action': "hold_flag_o = 1'b1;", 'block_path': ['0,0', '0,0,1']}, '0,0,0': {'condition': "!((int_state != 4'b0001) | (csr_state != 5'b00001))", 'action': "hold_flag_o = 1'b0;", 'block_path': ['0,0', '0,0,0']}}, {'1,0': {'condition': '', 'action': '', 'block_path': ['1,0']}, '1,0,1': {'condition': "(rst == 1'b0)", 'action': "int_state = 4'b0001;", 'block_path': ['1,0', '1,0,1']}, '1,0,0': {'condition': "!(rst == 1'b0)", 'action': '', 'block_path': ['1,0', '1,0,0']}, '1,0,0,1': {'condition': "(inst_i == 32'h73 || inst_i == 32'h00100073)", 'action': '', 'block_path': ['1,0', '1,0,0', '1,0,0,1']}, '1,0,0,1,1': {'condition': "(div_started_i == 1'b0)", 'action': "int_state = 4'b0010;", 'block_path': ['1,0', '1,0,0', '1,0,0,1', '1,0,0,1,1']}, '1,0,0,1,0': {'condition': "!(div_started_i == 1'b0)", 'action': "int_state = 4'b0001;", 'block_path': ['1,0', '1,0,0', '1,0,0,1', '1,0,0,1,0']}, '1,0,0,0': {'condition': "!(inst_i == 32'h73 || inst_i == 32'h00100073)", 'action': '', 'block_path': ['1,0', '1,0,0', '1,0,0,0']}, '1,0,0,0,1': {'condition': "(int_flag_i != 8'h0 && global_int_en_i == 1'b1)", 'action': "int_state = 4'b0100;", 'block_path': ['1,0', '1,0,0', '1,0,0,0', '1,0,0,0,1']}, '1,0,0,0,0': {'condition': "!(int_flag_i != 8'h0 && global_int_en_i == 1'b1)", 'action': '', 'block_path': ['1,0', '1,0,0', '1,0,0,0', '1,0,0,0,0']}, '1,0,0,0,0,1': {'condition': "(inst_i == 32'h30200073)", 'action': "int_state = 4'b1000;", 'block_path': ['1,0', '1,0,0', '1,0,0,0', '1,0,0,0,0', '1,0,0,0,0,1']}, '1,0,0,0,0,0': {'condition': "!(inst_i == 32'h30200073)", 'action': "int_state = 4'b0001;", 'block_path': ['1,0', '1,0,0', '1,0,0,0', '1,0,0,0,0', '1,0,0,0,0,0']}}, {'2,1': {'condition': '', 'action': '', 'block_path': ['2,1']}, '2,1,1': {'condition': "(rst == 1'b0)", 'action': "cause <= 32'h0;", 'block_path': ['2,1', '2,1,1']}, '2,1,0': {'condition': "!(rst == 1'b0)", 'action': "if(csr_state == 5'b00001 && int_state == 4'b0010)cause <= 32'd10;", 'block_path': ['2,1', '2,1,0']}, '2,1,0,1': {'condition': "(inst_i) == 32'h73", 'action': "cause <= 32'd11;", 'block_path': ['2,1', '2,1,0', '2,1,0,1']}, '2,1,0,2': {'condition': "(inst_i) == 32'h00100073", 'action': "cause <= 32'd3;", 'block_path': ['2,1', '2,1,0', '2,1,0,2']}, '2,1,0,3': {'condition': 'default', 'action': '', 'block_path': ['2,1', '2,1,0', '2,1,0,3']}, '2,0': {'condition': '!', 'action': '', 'block_path': ['2,0']}, '2,0,1': {'condition': "(int_state == 4'b0100)", 'action': "cause <= 32'h80000004;", 'block_path': ['2,0', '2,0,1']}}, {'3,1': {'condition': '', 'action': '', 'block_path': ['3,1']}, '3,1,1': {'condition': "(rst == 1'b0)", 'action': "csr_state <= 5'b00001;inst_addr <= 32'h0;", 'block_path': ['3,1', '3,1,1']}, '3,1,0': {'condition': "!(rst == 1'b0)", 'action': '', 'block_path': ['3,1', '3,1,0']}, '3,1,0,1': {'condition': "(csr_state) == 5'b00001", 'action': '', 'block_path': ['3,1', '3,1,0', '3,1,0,1']}, '3,1,0,1,1': {'condition': "(int_state == 4'b0010)", 'action': "csr_state <= 5'b00100;", 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,1']}, '3,1,0,1,1,1': {'condition': "(jump_flag_i == 1'b1)", 'action': "inst_addr <= jump_addr_i - 4'h4;", 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,1', '3,1,0,1,1,1']}, '3,1,0,1,1,0': {'condition': "!(jump_flag_i == 1'b1)", 'action': 'inst_addr <= inst_addr_i;', 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,1', '3,1,0,1,1,0']}, '3,1,0,1,0': {'condition': "!(int_state == 4'b0010)", 'action': '', 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0']}, '3,1,0,1,0,1': {'condition': "(int_state == 4'b0100)", 'action': "csr_state <= 5'b00100;", 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0', '3,1,0,1,0,1']}, '3,1,0,1,0,1,1': {'condition': "(jump_flag_i == 1'b1)", 'action': 'inst_addr <= jump_addr_i;', 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0', '3,1,0,1,0,1', '3,1,0,1,0,1,1']}, '3,1,0,1,0,1,0': {'condition': "!(jump_flag_i == 1'b1)", 'action': '', 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0', '3,1,0,1,0,1', '3,1,0,1,0,1,0']}, '3,1,0,1,0,1,0,1': {'condition': "(div_started_i == 1'b1)", 'action': "inst_addr <= inst_addr_i - 4'h4;", 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0', '3,1,0,1,0,1', '3,1,0,1,0,1,0', '3,1,0,1,0,1,0,1']}, '3,1,0,1,0,1,0,0': {'condition': "!(div_started_i == 1'b1)", 'action': 'inst_addr <= inst_addr_i;', 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0', '3,1,0,1,0,1', '3,1,0,1,0,1,0', '3,1,0,1,0,1,0,0']}, '3,1,0,1,0,0': {'condition': "!(int_state == 4'b0100)", 'action': '', 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0', '3,1,0,1,0,0']}, '3,1,0,1,0,0,1': {'condition': "(int_state == 4'b1000)", 'action': "csr_state <= 5'b01000;", 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0', '3,1,0,1,0,0', '3,1,0,1,0,0,1']}, '3,1,0,2': {'condition': "(csr_state) == 5'b00100", 'action': "csr_state <= 5'b00010;", 'block_path': ['3,1', '3,1,0', '3,1,0,2']}, '3,1,0,3': {'condition': "(csr_state) == 5'b00010", 'action': "csr_state <= 5'b10000;", 'block_path': ['3,1', '3,1,0', '3,1,0,3']}, '3,1,0,4': {'condition': "(csr_state) == 5'b10000", 'action': "csr_state <= 5'b00001;", 'block_path': ['3,1', '3,1,0', '3,1,0,4']}, '3,1,0,5': {'condition': "(csr_state) == 5'b01000", 'action': "csr_state <= 5'b00001;", 'block_path': ['3,1', '3,1,0', '3,1,0,5']}, '3,1,0,6': {'condition': 'default', 'action': "csr_state <= 5'b00001;", 'block_path': ['3,1', '3,1,0', '3,1,0,6']}}, {'4,1': {'condition': '', 'action': '', 'block_path': ['4,1']}, '4,1,1': {'condition': "(rst == 1'b0)", 'action': "we_o <= 1'b0;waddr_o <= 32'h0;data_o <= 32'h0;", 'block_path': ['4,1', '4,1,1']}, '4,1,0': {'condition': "!(rst == 1'b0)", 'action': "we_o <= 1'b0;waddr_o <= 32'h0;data_o <= 32'h0;", 'block_path': ['4,1', '4,1,0']}, '4,1,0,1': {'condition': "(csr_state) == 5'b00100", 'action': "we_o <= 1'b1;waddr_o <= {20'h0, 12'h341};data_o <= inst_addr;", 'block_path': ['4,1', '4,1,0', '4,1,0,1']}, '4,1,0,2': {'condition': "(csr_state) == 5'b10000", 'action': "we_o <= 1'b1;waddr_o <= {20'h0, 12'h342};data_o <= cause;", 'block_path': ['4,1', '4,1,0', '4,1,0,2']}, '4,1,0,3': {'condition': "(csr_state) == 5'b00010", 'action': "we_o <= 1'b1;waddr_o <= {20'h0, 12'h300};data_o <= {csr_mstatus[31:4], 1'b0, csr_mstatus[2:0]};", 'block_path': ['4,1', '4,1,0', '4,1,0,3']}, '4,1,0,4': {'condition': "(csr_state) == 5'b01000", 'action': "we_o <= 1'b1;waddr_o <= {20'h0, 12'h300};data_o <= {csr_mstatus[31:4], csr_mstatus[7], csr_mstatus[2:0]};", 'block_path': ['4,1', '4,1,0', '4,1,0,4']}, '4,1,0,5': {'condition': 'default', 'action': '', 'block_path': ['4,1', '4,1,0', '4,1,0,5']}}, {'5,1': {'condition': '', 'action': '', 'block_path': ['5,1']}, '5,1,1': {'condition': "(rst == 1'b0)", 'action': "int_assert_o <= 1'b0;int_addr_o <= 32'h0;", 'block_path': ['5,1', '5,1,1']}, '5,1,0': {'condition': "!(rst == 1'b0)", 'action': "int_assert_o <= 1'b0;int_addr_o <= 32'h0;", 'block_path': ['5,1', '5,1,0']}, '5,1,0,1': {'condition': "(csr_state) == 5'b10000", 'action': "int_assert_o <= 1'b1;int_addr_o <= csr_mtvec;", 'block_path': ['5,1', '5,1,0', '5,1,0,1']}, '5,1,0,2': {'condition': "(csr_state) == 5'b01000", 'action': "int_assert_o <= 1'b1;int_addr_o <= csr_mepc;", 'block_path': ['5,1', '5,1,0', '5,1,0,2']}, '5,1,0,3': {'condition': 'default', 'action': '', 'block_path': ['5,1', '5,1,0', '5,1,0,3']}}]

if __name__ == '__main__':
    # list_CDFG, list_inout = CDFG_1_1.main()
    signal_pattern = r'(?<!\')\b[a-zA-Z_]\w*\b'             # 匹配信号，但排除以单引号开头的数字常量
    constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量
    # in_1 = BitVec('in_1', 8)
    # clk = BitVec('clk', 1)
    # rst = BitVec('rst', 1)
    # out = BitVec('out', 8)
    # state = BitVec('state', 4)
    # st = BitVec('st', 4)
    # st2 = BitVec('st2', 4)

    # clk = BitVec('clk', 1)
    # W_in = BitVec('W_in', 1)
    # A_in = BitVec('A_in', 1)
    # sensor = BitVec('sensor', 1)
    # motor = BitVec('motor', 1)
    # next_state = BitVec('next_state', 2)
    # state = BitVec('state', 2)

    # clint.v
    clk = BitVec('clk', 1)
    rst = BitVec('rst', 1)
    inst_i = BitVec('inst_i', 32)
    inst_addr_i = BitVec('inst_addr_i', 32)
    jump_flag_i = BitVec('jump_flag_i', 1)
    jump_addr_i = BitVec('jump_addr_i', 32)
    div_started_i = BitVec('div_started_i', 1)
    hold_flag_i = BitVec('hold_flag_i', 3)
    data_i = BitVec('data_i', 32)
    csr_mtvec = BitVec('csr_mtvec', 32)
    csr_mepc = BitVec('csr_mepc', 32)
    csr_mstatus = BitVec('csr_mstatus', 32)
    global_int_en_i = BitVec('global_int_en_i', 1)
    hold_flag_o = BitVec('hold_flag_o', 1)
    we_o = BitVec('we_o', 1)
    waddr_o = BitVec('waddr_o', 32)
    raddr_o = BitVec('raddr_o', 32)
    data_o = BitVec('data_o', 32)
    int_addr_o = BitVec('int_addr_o', 32)
    int_assert_o = BitVec('int_assert_o', 1)
    inst_addr = BitVec('inst_addr', 32)
    cause = BitVec('cause', 32)
    int_state = BitVec('int_state', 4)
    csr_state = BitVec('csr_state', 5)

    # csr_reg.v
    # clk = BitVec('clk', 1)
    # rst = BitVec('rst', 1)
    # we_i = BitVec('we_i', 1)
    # raddr_i = BitVec('raddr_i', 32)
    # waddr_i = BitVec('waddr_i', 32)
    # data_i = BitVec('data_i', 32)
    # clint_we_i = BitVec('clint_we_i', 1)
    # clint_raddr_i = BitVec('clint_raddr_i', 32)
    # clint_waddr_i = BitVec('clint_waddr_i', 32)
    # clint_data_i = BitVec('clint_data_i', 32)
    # global_int_en_o = BitVec('global_int_en_o', 1)
    # clint_data_o = BitVec('clint_data_o', 32)
    # clint_csr_mtvec = BitVec('clint_csr_mtvec', 32)
    # clint_csr_mepc = BitVec('clint_csr_mepc', 32)
    # clint_csr_mstatus = BitVec('clint_csr_mstatus', 32)
    # data_o = BitVec('data_o', 32)
    # cycle = BitVec('cycle', 64)
    # mtvec = BitVec('mtvec', 32)
    # mcause = BitVec('mcause', 32)
    # mepc = BitVec('mepc', 32)
    # mie = BitVec('mie', 32)
    # mstatus = BitVec('mstatus', 32)
    # mscratch = BitVec('mscratch', 32)

    # uart_top.v
    # rec_dataH = BitVec('rec_dataH', 8)
    # rec_dataH_temp = BitVec('rec_dataH_temp', 8)
    # cntr = BitVec('cntr', 1)
    # rec_dataH_rec = BitVec('rec_dataH_rec', 8)
    # rec_readyH = BitVec('rec_readyH', 1)
    # next_state_xmit = BitVec('next_state_xmit', 3)
    # load_shiftRegH = BitVec('load_shiftRegH', 1)
    # shiftEnaH = BitVec('shiftEnaH', 1)
    # bitCell_cntrH = BitVec('bitCell_cntrH', 4)
    # countEnaH = BitVec('countEnaH', 1)
    # xmit_ShiftRegH = BitVec('xmit_ShiftRegH', 8)
    # bitCountH = BitVec('bitCountH', 4)
    # rst_bitCountH = BitVec('rst_bitCountH', 1)
    # ena_bitCountH = BitVec('ena_bitCountH', 1)
    # xmitDataSelH = BitVec('xmitDataSelH', 2)
    # uart_xmitH = BitVec('uart_xmitH', 1)
    # xmit_doneInH = BitVec('xmit_doneInH', 1)
    # xmit_doneH = BitVec('xmit_doneH', 1)
    # next_state_rec = BitVec('next_state_rec', 3)
    # rec_datH = BitVec('rec_datH', 1)
    # bitCell_cntrH_rec = BitVec('bitCell_cntrH_rec', 4)
    # cntr_resetH = BitVec('cntr_resetH', 1)
    # par_dataH = BitVec('par_dataH', 8)
    # shiftH = BitVec('shiftH', 1)
    # recd_bitCntrH = BitVec('recd_bitCntrH', 4)
    # countH = BitVec('countH', 1)
    # rstCountH = BitVec('rstCountH', 1)
    # rec_readyInH = BitVec('rec_readyInH', 1)
    # rec_dataH_1 = BitVec('rec_dataH_1', 8)
    # uart_dataH = BitVec('uart_dataH', 1)
    # xmit_dataH = BitVec('xmit_dataH', 8)
    # rec_datSyncH = BitVec('rec_datSyncH', 1)
    # uart_REC_dataH = BitVec('uart_REC_dataH', 1)
    # 定义全局变量，用于体现路径约减的效果
    num_all = 0
    num_apt = 0
    path_list = []
    constraint_stack = []
    flag = 0  # 用于控制路径搜索的回溯

    target_node = '5,1,0,2'
    num_start = 0  # 起始优先级
    # 输入reset信号名
    # reset_name = input('请输入reset信号名：')
    reset_name = 'rst'
    node_selected = []  # 用于记录以选择过的目标节点
    main()
    pass