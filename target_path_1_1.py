from math import *
import re
import os, glob
import argparse
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
                pass
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
    # 全局变量
    global num_all
    global num_apt
    global num_start
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
    pattern_1 = r'^(\d+\'[bdhBHD][0-9a-fA-F_]+|\d+)$'    # 匹配数字常量项
    dict_target_node = dict_CDFG_inout[target_node]      # 目标节点信息
    node_action_in = dict_target_node['action_in']
    node_action_in = list(set(node_action_in))
    node_action_in = list(filter(lambda x: not re.match(pattern_1, x), node_action_in))  # 排除数字常量项
    # node_action_out = dict_target_node['action_out']
    # node_condition_in = dict_target_node['condition_in']

    ############## 构造控制依赖信号列表 ########
    ctr_dep_list = []
    for node in path_in_block:
        if reset_name not in dict_CDFG_inout[node]['condition']:  # 排除reset信号
            ctr_dep_list.extend(dict_CDFG_inout[node]['condition_in'])
    ctr_dep_list = list(set(ctr_dep_list))
    
    ctr_dep_list = list(filter(lambda x: not re.match(pattern_1, x), ctr_dep_list))  # 排除数字常量项
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
                if reset_name in dict_CDFG_inout[key]['condition'] and key[-1] == '1':
                    sub_node_true = 0
                else:
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
    flag_in = 0
    ############## 数据依赖路径搭建#############
    for key, value in dict_CDFG_inout.items():           # 遍历所有节点
        sub_node_action_out = dict_CDFG_inout[key]['action_out']    # 提取可能上一级节点的输出信号
        path_list_D.append(target_node)                    # 开始构建目标路径
        for i in node_action_in:
            flag_in = 0
            if i.split('[')[0] in sub_node_action_out:
                if target_node != key:             # 排除自身节点,有利有弊,排除循环依赖
                    if reset_name not in dict_CDFG_inout[key]['condition']:
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
                        flag_in = 1
            if flag_in == 1:
                break
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
        # print(constraints)
        if constraints == []:
            print(f"存在循环依赖，路径{target_path}跳过")
        else:
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
            if constraints == []:
                print(f"存在循环依赖，路径{target_path}跳过")
                continue
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
                    constraint_stack = constraint_stack[:-1]  # 回溯
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
    # if flag_1 == len(path_l) and flag_1 != 0:
    #     num_start -= 1
    #     pass
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

def main_1(target_node_list, dict_CDFG_inout, reset_name):

    # 全局变量
    global num_all
    global num_apt
    global num_start
    global path_list
    global constraint_stack
    global flag

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

def main(deep, target_node, reset_name):
    # 全局变量
    global num_all
    global num_apt
    global path_list
    global constraint_stack
    global flag
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

    for i in range(deep):          # 手动定义路径搜寻深度
        print(f"已选择目标节点:{node_selected}")
        path_list = main_1(target_node_list, dict_CDFG_inout, reset_name)
        print(f"第{i+1}次搜索结果：{path_list}")
        target_node_list = []
        for j in range(len(path_list)):
            for k in range(len(path_list)):
                if path_list[j][0] == path_list[k][1]:
                    node_selected.append(path_list[j][0])
        for j in range(len(path_list)):
            if path_list[j][1] not in node_selected:
                target_node_list.append([path_list[j][1], path_list[j][4]+1])
            # if path_list[j][2] == '1':                 # 定位控制流末端
                # if path_list[j][1] not in node_selected:
                #     target_node_list.append([path_list[j][1],path_list[j][4]+1])  # [上级节点，距离]
                #     node_selected.append(path_list[j][1])
                # pass
        node_selected = list(set(node_selected))
        print(f"已选择目标节点:{node_selected}")
        print(f"目标节点列表：{target_node_list}")
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
    
# list_CDFG = [{'0,1': {'condition': '', 'action': '', 'block_path': ['0,1']}, '0,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "rst_cnt <= 5'h0;", 'block_path': ['0,1', '0,1,1']}, '0,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['0,1', '0,1,0']}, '0,1,0,1': {'condition': "(LineState_o != 2'h0)", 'action': "rst_cnt <= 5'h0;", 'block_path': ['0,1', '0,1,0', '0,1,0,1']}, '0,1,0,0': {'condition': "!(LineState_o != 2'h0)", 'action': '', 'block_path': ['0,1', '0,1,0', '0,1,0,0']}, '0,1,0,0,1': {'condition': '(!(usb_rst) && i_rx_phy_fs_ce)', 'action': "rst_cnt <= (rst_cnt + 5'h1);", 'block_path': ['0,1', '0,1,0', '0,1,0,0', '0,1,0,0,1']}}, {'1,1': {'condition': '', 'action': '', 'block_path': ['1,1']}, '1,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "usb_rst <= 1'b0;", 'block_path': ['1,1', '1,1,1']}, '1,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': "usb_rst <= (rst_cnt == 5'h1f);", 'block_path': ['1,1', '1,1,0']}}, {'2,0': {'condition': '', 'action': 'txdp = i_tx_phy_txdp;', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': 'txdn = i_tx_phy_txdn;', 'block_path': ['3,0']}}, {'4,0': {'condition': '', 'action': 'txoe = i_tx_phy_txoe;', 'block_path': ['4,0']}}, {'5,0': {'condition': '', 'action': 'TxReady_o = i_tx_phy_TxReady_o;', 'block_path': ['5,0']}}, {'6,1': {'condition': '', 'action': '', 'block_path': ['6,1']}, '6,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_TxReady_o <= 1'b0;", 'block_path': ['6,1', '6,1,1']}, '6,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_tx_phy_TxReady_o <= (i_tx_phy_tx_ready_d & TxValid_i);', 'block_path': ['6,1', '6,1,0']}}, {'7,1': {'condition': '', 'action': 'i_tx_phy_ld_data <= i_tx_phy_ld_data_d;', 'block_path': ['7,1']}}, {'8,1': {'condition': '', 'action': '', 'block_path': ['8,1']}, '8,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b0;", 'block_path': ['8,1', '8,1,1']}, '8,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['8,1', '8,1,0']}, '8,1,0,1': {'condition': "(i_tx_phy_ld_sop_d) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b1;", 'block_path': ['8,1', '8,1,0', '8,1,0,1']}, '8,1,0,0': {'condition': "!(i_tx_phy_ld_sop_d) == 1'b1", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,0']}, '8,1,0,0,1': {'condition': "(i_tx_phy_app_eop_sync3) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,0', '8,1,0,0,1']}}, {'9,1': {'condition': '', 'action': '', 'block_path': ['9,1']}, '9,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_tx_ip_sync <= 1'b0;", 'block_path': ['9,1', '9,1,1']}, '9,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['9,1', '9,1,0']}, '9,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_tx_ip_sync <= i_tx_phy_tx_ip;', 'block_path': ['9,1', '9,1,0', '9,1,0,1']}}, {'10,1': {'condition': '', 'action': '', 'block_path': ['10,1']}, '10,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_data_done <= 1'b0;", 'block_path': ['10,1', '10,1,1']}, '10,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['10,1', '10,1,0']}, '10,1,0,1': {'condition': '(TxValid_i && !(i_tx_phy_tx_ip))', 'action': "i_tx_phy_data_done <= 1'b1;", 'block_path': ['10,1', '10,1,0', '10,1,0,1']}, '10,1,0,0': {'condition': '!(TxValid_i && !(i_tx_phy_tx_ip))', 'action': '', 'block_path': ['10,1', '10,1,0', '10,1,0,0']}, '10,1,0,0,1': {'condition': "(!(TxValid_i)) == 1'b1", 'action': "i_tx_phy_data_done <= 1'b0;", 'block_path': ['10,1', '10,1,0', '10,1,0,0', '10,1,0,0,1']}}, {'11,1': {'condition': '', 'action': '', 'block_path': ['11,1']}, '11,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_bit_cnt <= 3'h0;", 'block_path': ['11,1', '11,1,1']}, '11,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['11,1', '11,1,0']}, '11,1,0,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_bit_cnt <= 3'h0;", 'block_path': ['11,1', '11,1,0', '11,1,0,1']}, '11,1,0,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['11,1', '11,1,0', '11,1,0,0']}, '11,1,0,0,1': {'condition': '(i_rx_phy_fs_ce && !(i_tx_phy_stuff))', 'action': "i_tx_phy_bit_cnt <= (i_tx_phy_bit_cnt + 3'h1);", 'block_path': ['11,1', '11,1,0', '11,1,0,0', '11,1,0,0,1']}}, {'12,1': {'condition': '', 'action': '', 'block_path': ['12,1']}, '12,1,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_sd_raw_o <= 1'b0;", 'block_path': ['12,1', '12,1,1']}, '12,1,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['12,1', '12,1,0']}, '12,1,0,1': {'condition': "(i_tx_phy_bit_cnt) == 3'h0", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[0];', 'block_path': ['12,1', '12,1,0', '12,1,0,1']}, '12,1,0,2': {'condition': "(i_tx_phy_bit_cnt) == 3'h1", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[1];', 'block_path': ['12,1', '12,1,0', '12,1,0,2']}, '12,1,0,3': {'condition': "(i_tx_phy_bit_cnt) == 3'h2", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[2];', 'block_path': ['12,1', '12,1,0', '12,1,0,3']}, '12,1,0,4': {'condition': "(i_tx_phy_bit_cnt) == 3'h3", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[3];', 'block_path': ['12,1', '12,1,0', '12,1,0,4']}, '12,1,0,5': {'condition': "(i_tx_phy_bit_cnt) == 3'h4", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[4];', 'block_path': ['12,1', '12,1,0', '12,1,0,5']}, '12,1,0,6': {'condition': "(i_tx_phy_bit_cnt) == 3'h5", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[5];', 'block_path': ['12,1', '12,1,0', '12,1,0,6']}, '12,1,0,7': {'condition': "(i_tx_phy_bit_cnt) == 3'h6", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[6];', 'block_path': ['12,1', '12,1,0', '12,1,0,7']}, '12,1,0,8': {'condition': "(i_tx_phy_bit_cnt) == 3'h7", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[7];', 'block_path': ['12,1', '12,1,0', '12,1,0,8']}}, {'13,1': {'condition': '', 'action': "i_tx_phy_sft_done <= (!((i_tx_phy_one_cnt == 3'h6)) & (i_tx_phy_bit_cnt == 3'h7));", 'block_path': ['13,1']}}, {'14,1': {'condition': '', 'action': 'i_tx_phy_sft_done_r <= i_tx_phy_sft_done;', 'block_path': ['14,1']}}, {'15,1': {'condition': '', 'action': '', 'block_path': ['15,1']}, '15,1,1': {'condition': "(i_tx_phy_ld_sop_d) == 1'b1", 'action': "i_tx_phy_hold_reg <= 8'h80;", 'block_path': ['15,1', '15,1,1']}, '15,1,0': {'condition': "!(i_tx_phy_ld_sop_d) == 1'b1", 'action': '', 'block_path': ['15,1', '15,1,0']}, '15,1,0,1': {'condition': "(i_tx_phy_ld_data) == 1'b1", 'action': 'i_tx_phy_hold_reg <= DataOut_i;', 'block_path': ['15,1', '15,1,0', '15,1,0,1']}}, {'16,1': {'condition': '', 'action': 'i_tx_phy_hold_reg_d <= i_tx_phy_hold_reg;', 'block_path': ['16,1']}}, {'17,1': {'condition': '', 'action': '', 'block_path': ['17,1']}, '17,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,1']}, '17,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0']}, '17,1,0,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,0', '17,1,0,1']}, '17,1,0,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0', '17,1,0,0']}, '17,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1']}, '17,1,0,0,1,1': {'condition': "(!(i_tx_phy_sd_raw_o) || (i_tx_phy_one_cnt == 3'h6))", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1', '17,1,0,0,1,1']}, '17,1,0,0,1,0': {'condition': "!(!(i_tx_phy_sd_raw_o) || (i_tx_phy_one_cnt == 3'h6))", 'action': "i_tx_phy_one_cnt <= (i_tx_phy_one_cnt + 3'h1);", 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1', '17,1,0,0,1,0']}}, {'18,0': {'condition': '', 'action': "i_tx_phy_stuff = (i_tx_phy_one_cnt == 3'h6);", 'block_path': ['18,0']}}, {'19,1': {'condition': '', 'action': '', 'block_path': ['19,1']}, '19,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_sd_bs_o <= 1'h0;", 'block_path': ['19,1', '19,1,1']}, '19,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['19,1', '19,1,0']}, '19,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_tx_phy_sd_bs_o <= ( ( !( i_tx_phy_tx_ip_sync) ) ? ( 1'b0 ) : ( ( ( ( i_tx_phy_one_cnt == 3'h6 ) ) ? ( 1'b0 ) : ( i_tx_phy_sd_raw_o ) ) ) );", 'block_path': ['19,1', '19,1,0', '19,1,0,1']}}, {'20,1': {'condition': '', 'action': '', 'block_path': ['20,1']}, '20,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_sd_nrzi_o <= 1'b1;", 'block_path': ['20,1', '20,1,1']}, '20,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['20,1', '20,1,0']}, '20,1,0,1': {'condition': '(!(i_tx_phy_tx_ip_sync) || !(i_tx_phy_txoe_r1))', 'action': "i_tx_phy_sd_nrzi_o <= 1'b1;", 'block_path': ['20,1', '20,1,0', '20,1,0,1']}, '20,1,0,0': {'condition': '!(!(i_tx_phy_tx_ip_sync) || !(i_tx_phy_txoe_r1))', 'action': '', 'block_path': ['20,1', '20,1,0', '20,1,0,0']}, '20,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_sd_nrzi_o <= ( ( i_tx_phy_sd_bs_o ) ? ( i_tx_phy_sd_nrzi_o ) : ( ~( i_tx_phy_sd_nrzi_o) ) );', 'block_path': ['20,1', '20,1,0', '20,1,0,0', '20,1,0,0,1']}}, {'21,1': {'condition': '', 'action': '', 'block_path': ['21,1']}, '21,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b0;", 'block_path': ['21,1', '21,1,1']}, '21,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['21,1', '21,1,0']}, '21,1,0,1': {'condition': "(i_tx_phy_ld_eop_d) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b1;", 'block_path': ['21,1', '21,1,0', '21,1,0,1']}, '21,1,0,0': {'condition': "!(i_tx_phy_ld_eop_d) == 1'b1", 'action': '', 'block_path': ['21,1', '21,1,0', '21,1,0,0']}, '21,1,0,0,1': {'condition': "(i_tx_phy_app_eop_sync2) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1']}}, {'22,1': {'condition': '', 'action': '', 'block_path': ['22,1']}, '22,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync1 <= 1'b0;", 'block_path': ['22,1', '22,1,1']}, '22,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['22,1', '22,1,0']}, '22,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync1 <= i_tx_phy_app_eop;', 'block_path': ['22,1', '22,1,0', '22,1,0,1']}}, {'23,1': {'condition': '', 'action': '', 'block_path': ['23,1']}, '23,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync2 <= 1'b0;", 'block_path': ['23,1', '23,1,1']}, '23,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['23,1', '23,1,0']}, '23,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync2 <= i_tx_phy_app_eop_sync1;', 'block_path': ['23,1', '23,1,0', '23,1,0,1']}}, {'24,1': {'condition': '', 'action': '', 'block_path': ['24,1']}, '24,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync3 <= 1'b0;", 'block_path': ['24,1', '24,1,1']}, '24,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['24,1', '24,1,0']}, '24,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync3 <= ( i_tx_phy_app_eop_sync2 | ( i_tx_phy_app_eop_sync3 & !( i_tx_phy_app_eop_sync4) ) );', 'block_path': ['24,1', '24,1,0', '24,1,0,1']}}, {'25,1': {'condition': '', 'action': '', 'block_path': ['25,1']}, '25,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync4 <= 1'b0;", 'block_path': ['25,1', '25,1,1']}, '25,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0']}, '25,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync4 <= i_tx_phy_app_eop_sync3;', 'block_path': ['25,1', '25,1,0', '25,1,0,1']}}, {'26,1': {'condition': '', 'action': '', 'block_path': ['26,1']}, '26,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe_r1 <= 1'b0;", 'block_path': ['26,1', '26,1,1']}, '26,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['26,1', '26,1,0']}, '26,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe_r1 <= i_tx_phy_tx_ip_sync;', 'block_path': ['26,1', '26,1,0', '26,1,0,1']}}, {'27,1': {'condition': '', 'action': '', 'block_path': ['27,1']}, '27,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe_r2 <= 1'b0;", 'block_path': ['27,1', '27,1,1']}, '27,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['27,1', '27,1,0']}, '27,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe_r2 <= i_tx_phy_txoe_r1;', 'block_path': ['27,1', '27,1,0', '27,1,0,1']}}, {'28,1': {'condition': '', 'action': '', 'block_path': ['28,1']}, '28,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe <= 1'b1;", 'block_path': ['28,1', '28,1,1']}, '28,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['28,1', '28,1,0']}, '28,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe <= !((i_tx_phy_txoe_r1 | i_tx_phy_txoe_r2));', 'block_path': ['28,1', '28,1,0', '28,1,0,1']}}, {'29,1': {'condition': '', 'action': '', 'block_path': ['29,1']}, '29,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txdp <= 1'b1;", 'block_path': ['29,1', '29,1,1']}, '29,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['29,1', '29,1,0']}, '29,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txdp <= ( ( phy_tx_mode ) ? ( ( !( i_tx_phy_app_eop_sync3) & i_tx_phy_sd_nrzi_o ) ) : ( i_tx_phy_sd_nrzi_o ) );', 'block_path': ['29,1', '29,1,0', '29,1,0,1']}}, {'30,1': {'condition': '', 'action': '', 'block_path': ['30,1']}, '30,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txdn <= 1'b0;", 'block_path': ['30,1', '30,1,1']}, '30,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['30,1', '30,1,0']}, '30,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txdn <= ( ( phy_tx_mode ) ? ( ( !( i_tx_phy_app_eop_sync3) & ~( i_tx_phy_sd_nrzi_o) ) ) : ( i_tx_phy_app_eop_sync3 ) );', 'block_path': ['30,1', '30,1,0', '30,1,0,1']}}, {'31,1': {'condition': '', 'action': '', 'block_path': ['31,1']}, '31,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_state <= 3'd0;", 'block_path': ['31,1', '31,1,1']}, '31,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_tx_phy_state <= i_tx_phy_next_state;', 'block_path': ['31,1', '31,1,0']}}, {'32,0': {'condition': '', 'action': "i_tx_phy_next_state = i_tx_phy_state;i_tx_phy_tx_ready_d = 1'b0;i_tx_phy_ld_sop_d = 1'b0;i_tx_phy_ld_data_d = 1'b0;i_tx_phy_ld_eop_d = 1'b0;", 'block_path': ['32,0']}, '32,0,1': {'condition': "(i_tx_phy_state) == 3'd0", 'action': '', 'block_path': ['32,0', '32,0,1']}, '32,0,1,1': {'condition': "(TxValid_i) == 1'b1", 'action': "i_tx_phy_ld_sop_d = 1'b1;i_tx_phy_next_state = 3'h1;", 'block_path': ['32,0', '32,0,1', '32,0,1,1']}, '32,0,2': {'condition': "(i_tx_phy_state) == 3'h1", 'action': '', 'block_path': ['32,0', '32,0,2']}, '32,0,2,1': {'condition': "(i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)) == 1'b1", 'action': "i_tx_phy_tx_ready_d = 1'b1;i_tx_phy_ld_data_d = 1'b1;i_tx_phy_next_state = 3'h2;", 'block_path': ['32,0', '32,0,2', '32,0,2,1']}, '32,0,3': {'condition': "(i_tx_phy_state) == 3'h2", 'action': '', 'block_path': ['32,0', '32,0,3']}, '32,0,3,1': {'condition': '(!(i_tx_phy_data_done) && (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)))', 'action': "i_tx_phy_ld_eop_d = 1'b1;i_tx_phy_next_state = 3'h3;", 'block_path': ['32,0', '32,0,3', '32,0,3,1']}, '32,0,3,1,1': {'condition': '(i_tx_phy_data_done && (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)))', 'action': "i_tx_phy_tx_ready_d = 1'b1;i_tx_phy_ld_data_d = 1'b1;", 'block_path': ['32,0', '32,0,3', '32,0,3,1', '32,0,3,1,1']}, '32,0,4': {'condition': "(i_tx_phy_state) == 3'h3", 'action': '', 'block_path': ['32,0', '32,0,4']}, '32,0,4,1': {'condition': "(i_tx_phy_app_eop_sync3) == 1'b1", 'action': "i_tx_phy_next_state = 3'h4;", 'block_path': ['32,0', '32,0,4', '32,0,4,1']}, '32,0,5': {'condition': "(i_tx_phy_state) == 3'h4", 'action': '', 'block_path': ['32,0', '32,0,5']}, '32,0,5,1': {'condition': '(!(i_tx_phy_app_eop_sync3) && i_rx_phy_fs_ce)', 'action': "i_tx_phy_next_state = 3'h5;", 'block_path': ['32,0', '32,0,5', '32,0,5,1']}, '32,0,6': {'condition': "(i_tx_phy_state) == 3'h5", 'action': '', 'block_path': ['32,0', '32,0,6']}, '32,0,6,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_tx_phy_next_state = 3'd0;", 'block_path': ['32,0', '32,0,6', '32,0,6,1']}}, {'33,0': {'condition': '', 'action': 'DataIn_o = i_rx_phy_hold_reg;', 'block_path': ['33,0']}}, {'34,0': {'condition': '', 'action': 'RxValid_o = i_rx_phy_rx_valid;', 'block_path': ['34,0']}}, {'35,0': {'condition': '', 'action': 'RxActive_o = i_rx_phy_rx_active;', 'block_path': ['35,0']}}, {'36,0': {'condition': '', 'action': 'RxError_o = ((i_rx_phy_sync_err | i_rx_phy_bit_stuff_err) | i_rx_phy_byte_err);', 'block_path': ['36,0']}}, {'37,0': {'condition': '', 'action': 'LineState_o = {i_rx_phy_rxdn_s1, i_rx_phy_rxdp_s1};', 'block_path': ['37,0']}}, {'38,1': {'condition': '', 'action': 'i_rx_phy_rx_en <= txoe;', 'block_path': ['38,1']}}, {'39,1': {'condition': '', 'action': 'i_rx_phy_sync_err <= (!(i_rx_phy_rx_active) & i_rx_phy_sync_err_d);', 'block_path': ['39,1']}}, {'40,1': {'condition': '', 'action': 'i_rx_phy_rxd_s0 <= rxd;', 'block_path': ['40,1']}}, {'41,1': {'condition': '', 'action': 'i_rx_phy_rxd_s1 <= i_rx_phy_rxd_s0;', 'block_path': ['41,1']}}, {'42,1': {'condition': '', 'action': '', 'block_path': ['42,1']}, '42,1,1': {'condition': '(i_rx_phy_rxd_s0 && i_rx_phy_rxd_s1)', 'action': "i_rx_phy_rxd_s <= 1'b1;", 'block_path': ['42,1', '42,1,1']}, '42,1,0': {'condition': '!(i_rx_phy_rxd_s0 && i_rx_phy_rxd_s1)', 'action': '', 'block_path': ['42,1', '42,1,0']}, '42,1,0,1': {'condition': '(!(i_rx_phy_rxd_s0) && !(i_rx_phy_rxd_s1))', 'action': "i_rx_phy_rxd_s <= 1'b0;", 'block_path': ['42,1', '42,1,0', '42,1,0,1']}}, {'43,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s0 <= rxdp;', 'block_path': ['43,1']}}, {'44,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s1 <= i_rx_phy_rxdp_s0;', 'block_path': ['44,1']}}, {'45,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s_r <= (i_rx_phy_rxdp_s0 & i_rx_phy_rxdp_s1);', 'block_path': ['45,1']}}, {'46,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s <= ((i_rx_phy_rxdp_s0 & i_rx_phy_rxdp_s1) | i_rx_phy_rxdp_s_r);', 'block_path': ['46,1']}}, {'47,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s0 <= rxdn;', 'block_path': ['47,1']}}, {'48,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s1 <= i_rx_phy_rxdn_s0;', 'block_path': ['48,1']}}, {'49,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s_r <= (i_rx_phy_rxdn_s0 & i_rx_phy_rxdn_s1);', 'block_path': ['49,1']}}, {'50,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s <= ((i_rx_phy_rxdn_s0 & i_rx_phy_rxdn_s1) | i_rx_phy_rxdn_s_r);', 'block_path': ['50,1']}}, {'51,1': {'condition': '', 'action': '', 'block_path': ['51,1']}, '51,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_se0_s <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s));', 'block_path': ['51,1', '51,1,1']}}, {'52,1': {'condition': '', 'action': 'i_rx_phy_rxd_r <= i_rx_phy_rxd_s;', 'block_path': ['52,1']}}, {'53,1': {'condition': '', 'action': '', 'block_path': ['53,1']}, '53,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_dpll_state <= 2'h1;", 'block_path': ['53,1', '53,1,1']}, '53,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_rx_phy_dpll_state <= i_rx_phy_dpll_next_state;', 'block_path': ['53,1', '53,1,0']}}, {'54,0': {'condition': '', 'action': "i_rx_phy_fs_ce_d = 1'b0;", 'block_path': ['54,0']}, '54,0,1': {'condition': "(i_rx_phy_dpll_state) == 2'h0", 'action': '', 'block_path': ['54,0', '54,0,1']}, '54,0,1,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,1', '54,0,1,1']}, '54,0,1,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h1;", 'block_path': ['54,0', '54,0,1', '54,0,1,0']}, '54,0,2': {'condition': "(i_rx_phy_dpll_state) == 2'h1", 'action': "i_rx_phy_fs_ce_d = 1'b1;", 'block_path': ['54,0', '54,0,2']}, '54,0,2,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h3;", 'block_path': ['54,0', '54,0,2', '54,0,2,1']}, '54,0,2,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h2;", 'block_path': ['54,0', '54,0,2', '54,0,2,0']}, '54,0,3': {'condition': "(i_rx_phy_dpll_state) == 2'h2", 'action': '', 'block_path': ['54,0', '54,0,3']}, '54,0,3,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,3', '54,0,3,1']}, '54,0,3,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h3;", 'block_path': ['54,0', '54,0,3', '54,0,3,0']}, '54,0,4': {'condition': "(i_rx_phy_dpll_state) == 2'h3", 'action': '', 'block_path': ['54,0', '54,0,4']}, '54,0,4,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,4', '54,0,4,1']}, '54,0,4,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,4', '54,0,4,0']}}, {'55,1': {'condition': '', 'action': 'i_rx_phy_fs_ce_r1 <= i_rx_phy_fs_ce_d;', 'block_path': ['55,1']}}, {'56,1': {'condition': '', 'action': 'i_rx_phy_fs_ce_r2 <= i_rx_phy_fs_ce_r1;', 'block_path': ['56,1']}}, {'57,1': {'condition': '', 'action': 'i_rx_phy_fs_ce <= i_rx_phy_fs_ce_r2;', 'block_path': ['57,1']}}, {'58,1': {'condition': '', 'action': '', 'block_path': ['58,1']}, '58,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_fs_state <= 3'h0;", 'block_path': ['58,1', '58,1,1']}, '58,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_rx_phy_fs_state <= i_rx_phy_fs_next_state;', 'block_path': ['58,1', '58,1,0']}}, {'59,0': {'condition': '', 'action': "i_rx_phy_synced_d = 1'b0;i_rx_phy_sync_err_d = 1'b0;i_rx_phy_fs_next_state = i_rx_phy_fs_state;", 'block_path': ['59,0']}, '59,0,1': {'condition': '( ( ( i_rx_phy_fs_ce && !( i_rx_phy_rx_active) ) && !( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) )) ) && !( i_rx_phy_se0_s) )', 'action': '', 'block_path': ['59,0', '59,0,1']}, '59,0,1,1': {'condition': "(i_rx_phy_fs_state) == 3'h0", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,1']}, '59,0,1,1,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h1;", 'block_path': ['59,0', '59,0,1', '59,0,1,1', '59,0,1,1,1']}, '59,0,1,2': {'condition': "(i_rx_phy_fs_state) == 3'h1", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,2']}, '59,0,1,2,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h2;", 'block_path': ['59,0', '59,0,1', '59,0,1,2', '59,0,1,2,1']}, '59,0,1,2,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,2', '59,0,1,2,0']}, '59,0,1,3': {'condition': "(i_rx_phy_fs_state) == 3'h2", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,3']}, '59,0,1,3,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h3;", 'block_path': ['59,0', '59,0,1', '59,0,1,3', '59,0,1,3,1']}, '59,0,1,3,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,3', '59,0,1,3,0']}, '59,0,1,4': {'condition': "(i_rx_phy_fs_state) == 3'h3", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,4']}, '59,0,1,4,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h4;", 'block_path': ['59,0', '59,0,1', '59,0,1,4', '59,0,1,4,1']}, '59,0,1,4,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,4', '59,0,1,4,0']}, '59,0,1,5': {'condition': "(i_rx_phy_fs_state) == 3'h4", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,5']}, '59,0,1,5,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h5;", 'block_path': ['59,0', '59,0,1', '59,0,1,5', '59,0,1,5,1']}, '59,0,1,5,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,5', '59,0,1,5,0']}, '59,0,1,6': {'condition': "(i_rx_phy_fs_state) == 3'h5", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,6']}, '59,0,1,6,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h6;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,1']}, '59,0,1,6,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0']}, '59,0,1,6,0,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h0;i_rx_phy_synced_d = 1'b1;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0', '59,0,1,6,0,1']}, '59,0,1,6,0,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0', '59,0,1,6,0,0']}, '59,0,1,7': {'condition': "(i_rx_phy_fs_state) == 3'h6", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,7']}, '59,0,1,7,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h7;", 'block_path': ['59,0', '59,0,1', '59,0,1,7', '59,0,1,7,1']}, '59,0,1,7,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,7', '59,0,1,7,0']}, '59,0,1,8': {'condition': "(i_rx_phy_fs_state) == 3'h7", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,8']}, '59,0,1,8,1': {'condition': "(!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) == 1'b1", 'action': "i_rx_phy_synced_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,8', '59,0,1,8,1']}}, {'60,1': {'condition': '', 'action': '', 'block_path': ['60,1']}, '60,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_rx_active <= 1'b0;", 'block_path': ['60,1', '60,1,1']}, '60,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['60,1', '60,1,0']}, '60,1,0,1': {'condition': '(i_rx_phy_synced_d && i_rx_phy_rx_en)', 'action': "i_rx_phy_rx_active <= 1'b1;", 'block_path': ['60,1', '60,1,0', '60,1,0,1']}, '60,1,0,0': {'condition': '!(i_rx_phy_synced_d && i_rx_phy_rx_en)', 'action': '', 'block_path': ['60,1', '60,1,0', '60,1,0,0']}, '60,1,0,0,1': {'condition': '((!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_valid_r)', 'action': "i_rx_phy_rx_active <= 1'b0;", 'block_path': ['60,1', '60,1,0', '60,1,0,0', '60,1,0,0,1']}}, {'61,1': {'condition': '', 'action': '', 'block_path': ['61,1']}, '61,1,1': {'condition': "(i_rx_phy_rx_valid) == 1'b1", 'action': "i_rx_phy_rx_valid_r <= 1'b1;", 'block_path': ['61,1', '61,1,1']}, '61,1,0': {'condition': "!(i_rx_phy_rx_valid) == 1'b1", 'action': '', 'block_path': ['61,1', '61,1,0']}, '61,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_rx_phy_rx_valid_r <= 1'b0;", 'block_path': ['61,1', '61,1,0', '61,1,0,1']}}, {'62,1': {'condition': '', 'action': '', 'block_path': ['62,1']}, '62,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_sd_r <= i_rx_phy_rxd_s;', 'block_path': ['62,1', '62,1,1']}}, {'63,1': {'condition': '', 'action': '', 'block_path': ['63,1']}, '63,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_sd_nrzi <= 1'b0;", 'block_path': ['63,1', '63,1,1']}, '63,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['63,1', '63,1,0']}, '63,1,0,1': {'condition': "(!(i_rx_phy_rx_active)) == 1'b1", 'action': "i_rx_phy_sd_nrzi <= 1'b1;", 'block_path': ['63,1', '63,1,0', '63,1,0,1']}, '63,1,0,0': {'condition': "!(!(i_rx_phy_rx_active)) == 1'b1", 'action': '', 'block_path': ['63,1', '63,1,0', '63,1,0,0']}, '63,1,0,0,1': {'condition': '(i_rx_phy_rx_active && i_rx_phy_fs_ce)', 'action': 'i_rx_phy_sd_nrzi <= !((i_rx_phy_rxd_s ^ i_rx_phy_sd_r));', 'block_path': ['63,1', '63,1,0', '63,1,0,0', '63,1,0,0,1']}}, {'64,1': {'condition': '', 'action': '', 'block_path': ['64,1']}, '64,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,1']}, '64,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0']}, '64,1,0,1': {'condition': "(!(i_rx_phy_shift_en)) == 1'b1", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,0', '64,1,0,1']}, '64,1,0,0': {'condition': "!(!(i_rx_phy_shift_en)) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0', '64,1,0,0']}, '64,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1']}, '64,1,0,0,1,1': {'condition': "(!(i_rx_phy_sd_nrzi) || (i_rx_phy_one_cnt == 3'h6))", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1', '64,1,0,0,1,1']}, '64,1,0,0,1,0': {'condition': "!(!(i_rx_phy_sd_nrzi) || (i_rx_phy_one_cnt == 3'h6))", 'action': "i_rx_phy_one_cnt <= (i_rx_phy_one_cnt + 3'h1);", 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1', '64,1,0,0,1,0']}}, {'65,1': {'condition': '', 'action': "i_rx_phy_bit_stuff_err <= ( ( ( ( ( i_rx_phy_one_cnt == 3'h6 ) & i_rx_phy_sd_nrzi ) & i_rx_phy_fs_ce ) & !( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) )) ) & i_rx_phy_rx_active );", 'block_path': ['65,1']}}, {'66,1': {'condition': '', 'action': '', 'block_path': ['66,1']}, '66,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_shift_en <= (i_rx_phy_synced_d | i_rx_phy_rx_active);', 'block_path': ['66,1', '66,1,1']}}, {'67,1': {'condition': '', 'action': '', 'block_path': ['67,1']}, '67,1,1': {'condition': "((i_rx_phy_fs_ce && i_rx_phy_shift_en) && !((i_rx_phy_one_cnt == 3'h6)))", 'action': 'i_rx_phy_hold_reg <= {i_rx_phy_sd_nrzi, i_rx_phy_hold_reg[7:1]};', 'block_path': ['67,1', '67,1,1']}}, {'68,1': {'condition': '', 'action': '', 'block_path': ['68,1']}, '68,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_bit_cnt <= 3'b0;", 'block_path': ['68,1', '68,1,1']}, '68,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['68,1', '68,1,0']}, '68,1,0,1': {'condition': "(!(i_rx_phy_shift_en)) == 1'b1", 'action': "i_rx_phy_bit_cnt <= 3'h0;", 'block_path': ['68,1', '68,1,0', '68,1,0,1']}, '68,1,0,0': {'condition': "!(!(i_rx_phy_shift_en)) == 1'b1", 'action': '', 'block_path': ['68,1', '68,1,0', '68,1,0,0']}, '68,1,0,0,1': {'condition': "(i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6)))", 'action': "i_rx_phy_bit_cnt <= (i_rx_phy_bit_cnt + 3'h1);", 'block_path': ['68,1', '68,1,0', '68,1,0,0', '68,1,0,0,1']}}, {'69,1': {'condition': '', 'action': '', 'block_path': ['69,1']}, '69,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_rx_valid1 <= 1'b0;", 'block_path': ['69,1', '69,1,1']}, '69,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['69,1', '69,1,0']}, '69,1,0,1': {'condition': "((i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6))) && (i_rx_phy_bit_cnt == 3'h7))", 'action': "i_rx_phy_rx_valid1 <= 1'b1;", 'block_path': ['69,1', '69,1,0', '69,1,0,1']}, '69,1,0,0': {'condition': "!((i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6))) && (i_rx_phy_bit_cnt == 3'h7))", 'action': '', 'block_path': ['69,1', '69,1,0', '69,1,0,0']}, '69,1,0,0,1': {'condition': "((i_rx_phy_rx_valid1 && i_rx_phy_fs_ce) && !((i_rx_phy_one_cnt == 3'h6)))", 'action': "i_rx_phy_rx_valid1 <= 1'b0;", 'block_path': ['69,1', '69,1,0', '69,1,0,0', '69,1,0,0,1']}}, {'70,1': {'condition': '', 'action': "i_rx_phy_rx_valid <= ((!((i_rx_phy_one_cnt == 3'h6)) & i_rx_phy_rx_valid1) & i_rx_phy_fs_ce);", 'block_path': ['70,1']}}, {'71,1': {'condition': '', 'action': 'i_rx_phy_se0_r <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s));', 'block_path': ['71,1']}}, {'72,1': {'condition': '', 'action': 'i_rx_phy_byte_err <= ( ( ( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) ) & !( i_rx_phy_se0_r) ) & |( i_rx_phy_bit_cnt[2:1]) ) & i_rx_phy_rx_active );', 'block_path': ['72,1']}}]

list_CDFG = [{'0,0': {'condition': '', 'action': 'trigger = signal1 & signal2 & signal3;', 'block_path': ['0,0']}}, {'1,1': {'condition': '', 'action': '', 'block_path': ['1,1']}, '1,1,1': {'condition': "(rst) == 1'b1", 'action': "signal1 <= 1'b0;signal2 <= 1'b0;signal3 <= 1'b0;", 'block_path': ['1,1', '1,1,1']}, '1,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['1,1', '1,1,0']}, '1,1,0,1': {'condition': "(input_a == 32'h11223344)", 'action': "signal2 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,1']}, '1,1,0,0': {'condition': "!(input_a == 32'h11223344)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,0']}, '1,1,0,0,1': {'condition': "(input_b == 32'h55667788 && signal1)", 'action': "signal3 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,1']}, '1,1,0,0,0': {'condition': "!(input_b == 32'h55667788 && signal1)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0']}, '1,1,0,0,0,1': {'condition': "(input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2)", 'action': "signal1 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0', '1,1,0,0,0,1']}, '1,1,0,0,0,0': {'condition': "!(input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2)", 'action': "signal1 <= 1'b0;signal2 <= 1'b0;signal3 <= 1'b0;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0', '1,1,0,0,0,0']}}, {'2,1': {'condition': '', 'action': 'ctr_1 <= ctr;', 'block_path': ['2,1']}}, {'3,1': {'condition': '', 'action': 'ctr_2 <= ctr_1;', 'block_path': ['3,1']}}, {'4,1': {'condition': '', 'action': '', 'block_path': ['4,1']}, '4,1,1': {'condition': "(rst) == 1'b1", 'action': "ht_out <= 32'b0;", 'block_path': ['4,1', '4,1,1']}, '4,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['4,1', '4,1,0']}, '4,1,0,1': {'condition': "(ctr_2 == 32'h12345678)", 'action': '', 'block_path': ['4,1', '4,1,0', '4,1,0,1']}, '4,1,0,1,1': {'condition': "(trigger == 1'b1)", 'action': "ht_out <= {ht_out[30:0], ht_out[31] ^ 1'b1};", 'block_path': ['4,1', '4,1,0', '4,1,0,1', '4,1,0,1,1']}, '4,1,0,1,0': {'condition': "!(trigger == 1'b1)", 'action': 'ht_out <= {ht_out[30:0], ht_out[31]};', 'block_path': ['4,1', '4,1,0', '4,1,0,1', '4,1,0,1,0']}, '4,1,0,0': {'condition': "!(ctr_2 == 32'h12345678)", 'action': 'ht_out <= ht_out;', 'block_path': ['4,1', '4,1,0', '4,1,0,0']}}]

list_CDFG = [{'0,0': {'condition': '', 'action': "st = state + 4'h2;", 'block_path': ['0,0']}}, {'1,0': {'condition': '', 'action': 'st2 = st;', 'block_path': ['1,0']}}, {'2,1': {'condition': '', 'action': '', 'block_path': ['2,1']}, '2,1,1': {'condition': "(rst) == 1'b1", 'action': "state <= 4'h0;", 'block_path': ['2,1', '2,1,1']}, '2,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['2,1', '2,1,0']}, '2,1,0,1': {'condition': "(in_1 == 8'h26)", 'action': "state <= 4'h1;", 'block_path': ['2,1', '2,1,0', '2,1,0,1']}, '2,1,0,0': {'condition': "!(in_1 == 8'h26)", 'action': '', 'block_path': ['2,1', '2,1,0', '2,1,0,0']}, '2,1,0,0,1': {'condition': "(in_1 == 8'hf5 && state == 4'h1)", 'action': "state <= 4'h2;", 'block_path': ['2,1', '2,1,0', '2,1,0,0', '2,1,0,0,1']}, '2,1,0,0,0': {'condition': "!(in_1 == 8'hf5 && state == 4'h1)", 'action': '', 'block_path': ['2,1', '2,1,0', '2,1,0,0', '2,1,0,0,0']}, '2,1,0,0,0,1': {'condition': "(in_1 == 8'h6e && state == 4'h2)", 'action': "state <= 4'h3;", 'block_path': ['2,1', '2,1,0', '2,1,0,0', '2,1,0,0,0', '2,1,0,0,0,1']}, '2,1,0,0,0,0': {'condition': "!(in_1 == 8'h6e && state == 4'h2)", 'action': "state <= 4'h0;", 'block_path': ['2,1', '2,1,0', '2,1,0,0', '2,1,0,0,0', '2,1,0,0,0,0']}}, {'3,1': {'condition': '', 'action': '', 'block_path': ['3,1']}, '3,1,1': {'condition': "(rst) == 1'b1", 'action': "out <= 8'b0;", 'block_path': ['3,1', '3,1,1']}, '3,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['3,1', '3,1,0']}, '3,1,0,1': {'condition': "(st2 == 4'h5)", 'action': 'out <= 1;', 'block_path': ['3,1', '3,1,0', '3,1,0,1']}}]
if __name__ == '__main__':
    # list_CDFG, list_inout = CDFG_1_1.main()
    signal_pattern = r'(?<!\')\b[a-zA-Z_]\w*\b'             # 匹配信号，但排除以单引号开头的数字常量
    constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量

    # case1
    in_1 = BitVec('in_1', 8)
    out = BitVec('out', 8)
    clk = BitVec('clk', 1)
    state = BitVec('state', 4)
    st = BitVec('st', 4)
    st2 = BitVec('st2', 4)

    # case3
    # clk = BitVec('clk', 1)
    # rst = BitVec('rst', 1)
    # input_a = BitVec('input_a', 32)
    # input_b = BitVec('input_b', 32)
    # ctr = BitVec('ctr', 32)
    # ctr_1 = BitVec('ctr', 32)
    # ctr_2 = BitVec('ctr', 32)
    # ht_out = BitVec('ht_out', 32)
    # signal1 = BitVec('signal1', 1)
    # signal2 = BitVec('signal1', 1)
    # signal3 = BitVec('signal1', 1)
    # trigger = BitVec('trigger', 1)


    # b10.v
    # r_button = BitVec('r_button', 1)
    # g_button = BitVec('g_button', 1)
    # key = BitVec('key', 1)
    # start = BitVec('start', 1)
    # reset = BitVec('reset', 1)
    # test = BitVec('test', 1)
    # cts = BitVec('cts', 1)
    # ctr = BitVec('ctr', 1)
    # rts = BitVec('rts', 1)
    # rtr = BitVec('rtr', 1)
    # clock = BitVec('clock', 1)
    # v_in = BitVec('v_in', 4)
    # v_out = BitVec('v_out', 4)
    # stato = BitVec('stato', 4)
    # voto0 = BitVec('voto0', 1)
    # voto1 = BitVec('voto1', 1)
    # voto2 = BitVec('voto2', 1)
    # voto3 = BitVec('voto3', 1)
    # sign = BitVec('sign', 4)
    # last_g = BitVec('last_g', 1)
    # last_r = BitVec('last_r', 1)

    # usb_phy.v
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

    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='自动化参数配置工具',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 添加参数定义
    parser.add_argument('deep', type=int, default=1,
                      help='遍历深度级别 (必须 ≥1)')
    parser.add_argument('target_node', type=str, default='0,0',
                      help='目标节点坐标，格式为逗号分隔字符串')
    parser.add_argument('reset_name', type=str, default='rst',
                      help='复位信号名称')
    
    # 解析参数
    args = parser.parse_args()
    # 参数验证
    if args.deep < 1:
        raise ValueError("遍历深度必须 ≥1")
    if not all(part.isdigit() for part in args.target_node.split(',')):
        raise ValueError("目标节点坐标必须为数字逗号分隔格式")


    # 定义全局变量，用于体现路径约减的效果
    num_all = 0
    num_apt = 0
    path_list = []
    constraint_stack = []
    flag = 0  # 用于控制路径搜索的回溯

    deep = args.deep
    target_node = args.target_node
    reset_name = args.reset_name
    num_start = 0  # 起始优先级    
    node_selected = []  # 用于记录以选择过的目标节点
    main(deep, target_node, reset_name)
    pass