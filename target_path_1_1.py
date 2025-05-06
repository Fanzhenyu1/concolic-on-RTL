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

def get_CDFG():
    return list_CDFG

# usb_phy    
# list_CDFG = [{'0,1': {'condition': '', 'action': '', 'block_path': ['0,1']}, '0,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "rst_cnt <= 5'h0;", 'block_path': ['0,1', '0,1,1']}, '0,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['0,1', '0,1,0']}, '0,1,0,1': {'condition': "(LineState_o != 2'h0)", 'action': "rst_cnt <= 5'h0;", 'block_path': ['0,1', '0,1,0', '0,1,0,1']}, '0,1,0,0': {'condition': "!(LineState_o != 2'h0)", 'action': '', 'block_path': ['0,1', '0,1,0', '0,1,0,0']}, '0,1,0,0,1': {'condition': '(!(usb_rst) && i_rx_phy_fs_ce)', 'action': "rst_cnt <= (rst_cnt + 5'h1);", 'block_path': ['0,1', '0,1,0', '0,1,0,0', '0,1,0,0,1']}}, {'1,1': {'condition': '', 'action': '', 'block_path': ['1,1']}, '1,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "usb_rst <= 1'b0;", 'block_path': ['1,1', '1,1,1']}, '1,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': "usb_rst <= (rst_cnt == 5'h1f);", 'block_path': ['1,1', '1,1,0']}}, {'2,0': {'condition': '', 'action': 'txdp = i_tx_phy_txdp;', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': 'txdn = i_tx_phy_txdn;', 'block_path': ['3,0']}}, {'4,0': {'condition': '', 'action': 'txoe = i_tx_phy_txoe;', 'block_path': ['4,0']}}, {'5,0': {'condition': '', 'action': 'TxReady_o = i_tx_phy_TxReady_o;', 'block_path': ['5,0']}}, {'6,1': {'condition': '', 'action': '', 'block_path': ['6,1']}, '6,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_TxReady_o <= 1'b0;", 'block_path': ['6,1', '6,1,1']}, '6,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_tx_phy_TxReady_o <= (i_tx_phy_tx_ready_d & TxValid_i);', 'block_path': ['6,1', '6,1,0']}}, {'7,1': {'condition': '', 'action': 'i_tx_phy_ld_data <= i_tx_phy_ld_data_d;', 'block_path': ['7,1']}}, {'8,1': {'condition': '', 'action': '', 'block_path': ['8,1']}, '8,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b0;", 'block_path': ['8,1', '8,1,1']}, '8,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['8,1', '8,1,0']}, '8,1,0,1': {'condition': "(i_tx_phy_ld_sop_d) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b1;", 'block_path': ['8,1', '8,1,0', '8,1,0,1']}, '8,1,0,0': {'condition': "!(i_tx_phy_ld_sop_d) == 1'b1", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,0']}, '8,1,0,0,1': {'condition': "(i_tx_phy_app_eop_sync3) == 1'b1", 'action': "i_tx_phy_tx_ip <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,0', '8,1,0,0,1']}}, {'9,1': {'condition': '', 'action': '', 'block_path': ['9,1']}, '9,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_tx_ip_sync <= 1'b0;", 'block_path': ['9,1', '9,1,1']}, '9,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['9,1', '9,1,0']}, '9,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_tx_ip_sync <= i_tx_phy_tx_ip;', 'block_path': ['9,1', '9,1,0', '9,1,0,1']}}, {'10,1': {'condition': '', 'action': '', 'block_path': ['10,1']}, '10,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_data_done <= 1'b0;", 'block_path': ['10,1', '10,1,1']}, '10,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['10,1', '10,1,0']}, '10,1,0,1': {'condition': '(TxValid_i && !(i_tx_phy_tx_ip))', 'action': "i_tx_phy_data_done <= 1'b1;", 'block_path': ['10,1', '10,1,0', '10,1,0,1']}, '10,1,0,0': {'condition': '!(TxValid_i && !(i_tx_phy_tx_ip))', 'action': '', 'block_path': ['10,1', '10,1,0', '10,1,0,0']}, '10,1,0,0,1': {'condition': "(!(TxValid_i)) == 1'b1", 'action': "i_tx_phy_data_done <= 1'b0;", 'block_path': ['10,1', '10,1,0', '10,1,0,0', '10,1,0,0,1']}}, {'11,1': {'condition': '', 'action': '', 'block_path': ['11,1']}, '11,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_bit_cnt <= 3'h0;", 'block_path': ['11,1', '11,1,1']}, '11,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['11,1', '11,1,0']}, '11,1,0,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_bit_cnt <= 3'h0;", 'block_path': ['11,1', '11,1,0', '11,1,0,1']}, '11,1,0,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['11,1', '11,1,0', '11,1,0,0']}, '11,1,0,0,1': {'condition': '(i_rx_phy_fs_ce && !(i_tx_phy_stuff))', 'action': "i_tx_phy_bit_cnt <= (i_tx_phy_bit_cnt + 3'h1);", 'block_path': ['11,1', '11,1,0', '11,1,0,0', '11,1,0,0,1']}}, {'12,1': {'condition': '', 'action': '', 'block_path': ['12,1']}, '12,1,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_sd_raw_o <= 1'b0;", 'block_path': ['12,1', '12,1,1']}, '12,1,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['12,1', '12,1,0']}, '12,1,0,1': {'condition': "(i_tx_phy_bit_cnt) == 3'h0", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[0];', 'block_path': ['12,1', '12,1,0', '12,1,0,1']}, '12,1,0,2': {'condition': "(i_tx_phy_bit_cnt) == 3'h1", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[1];', 'block_path': ['12,1', '12,1,0', '12,1,0,2']}, '12,1,0,3': {'condition': "(i_tx_phy_bit_cnt) == 3'h2", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[2];', 'block_path': ['12,1', '12,1,0', '12,1,0,3']}, '12,1,0,4': {'condition': "(i_tx_phy_bit_cnt) == 3'h3", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[3];', 'block_path': ['12,1', '12,1,0', '12,1,0,4']}, '12,1,0,5': {'condition': "(i_tx_phy_bit_cnt) == 3'h4", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[4];', 'block_path': ['12,1', '12,1,0', '12,1,0,5']}, '12,1,0,6': {'condition': "(i_tx_phy_bit_cnt) == 3'h5", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[5];', 'block_path': ['12,1', '12,1,0', '12,1,0,6']}, '12,1,0,7': {'condition': "(i_tx_phy_bit_cnt) == 3'h6", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[6];', 'block_path': ['12,1', '12,1,0', '12,1,0,7']}, '12,1,0,8': {'condition': "(i_tx_phy_bit_cnt) == 3'h7", 'action': 'i_tx_phy_sd_raw_o <= i_tx_phy_hold_reg_d[7];', 'block_path': ['12,1', '12,1,0', '12,1,0,8']}}, {'13,1': {'condition': '', 'action': "i_tx_phy_sft_done <= (!((i_tx_phy_one_cnt == 3'h6)) & (i_tx_phy_bit_cnt == 3'h7));", 'block_path': ['13,1']}}, {'14,1': {'condition': '', 'action': 'i_tx_phy_sft_done_r <= i_tx_phy_sft_done;', 'block_path': ['14,1']}}, {'15,1': {'condition': '', 'action': '', 'block_path': ['15,1']}, '15,1,1': {'condition': "(i_tx_phy_ld_sop_d) == 1'b1", 'action': "i_tx_phy_hold_reg <= 8'h80;", 'block_path': ['15,1', '15,1,1']}, '15,1,0': {'condition': "!(i_tx_phy_ld_sop_d) == 1'b1", 'action': '', 'block_path': ['15,1', '15,1,0']}, '15,1,0,1': {'condition': "(i_tx_phy_ld_data) == 1'b1", 'action': 'i_tx_phy_hold_reg <= DataOut_i;', 'block_path': ['15,1', '15,1,0', '15,1,0,1']}}, {'16,1': {'condition': '', 'action': 'i_tx_phy_hold_reg_d <= i_tx_phy_hold_reg;', 'block_path': ['16,1']}}, {'17,1': {'condition': '', 'action': '', 'block_path': ['17,1']}, '17,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,1']}, '17,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0']}, '17,1,0,1': {'condition': "(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,0', '17,1,0,1']}, '17,1,0,0': {'condition': "!(!(i_tx_phy_tx_ip_sync)) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0', '17,1,0,0']}, '17,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': '', 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1']}, '17,1,0,0,1,1': {'condition': "(!(i_tx_phy_sd_raw_o) || (i_tx_phy_one_cnt == 3'h6))", 'action': "i_tx_phy_one_cnt <= 3'h0;", 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1', '17,1,0,0,1,1']}, '17,1,0,0,1,0': {'condition': "!(!(i_tx_phy_sd_raw_o) || (i_tx_phy_one_cnt == 3'h6))", 'action': "i_tx_phy_one_cnt <= (i_tx_phy_one_cnt + 3'h1);", 'block_path': ['17,1', '17,1,0', '17,1,0,0', '17,1,0,0,1', '17,1,0,0,1,0']}}, {'18,0': {'condition': '', 'action': "i_tx_phy_stuff = (i_tx_phy_one_cnt == 3'h6);", 'block_path': ['18,0']}}, {'19,1': {'condition': '', 'action': '', 'block_path': ['19,1']}, '19,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_sd_bs_o <= 1'h0;", 'block_path': ['19,1', '19,1,1']}, '19,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['19,1', '19,1,0']}, '19,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_tx_phy_sd_bs_o <= ( ( !( i_tx_phy_tx_ip_sync) ) ? ( 1'b0 ) : ( ( ( ( i_tx_phy_one_cnt == 3'h6 ) ) ? ( 1'b0 ) : ( i_tx_phy_sd_raw_o ) ) ) );", 'block_path': ['19,1', '19,1,0', '19,1,0,1']}}, {'20,1': {'condition': '', 'action': '', 'block_path': ['20,1']}, '20,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_sd_nrzi_o <= 1'b1;", 'block_path': ['20,1', '20,1,1']}, '20,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['20,1', '20,1,0']}, '20,1,0,1': {'condition': '(!(i_tx_phy_tx_ip_sync) || !(i_tx_phy_txoe_r1))', 'action': "i_tx_phy_sd_nrzi_o <= 1'b1;", 'block_path': ['20,1', '20,1,0', '20,1,0,1']}, '20,1,0,0': {'condition': '!(!(i_tx_phy_tx_ip_sync) || !(i_tx_phy_txoe_r1))', 'action': '', 'block_path': ['20,1', '20,1,0', '20,1,0,0']}, '20,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_sd_nrzi_o <= ( ( i_tx_phy_sd_bs_o ) ? ( i_tx_phy_sd_nrzi_o ) : ( ~( i_tx_phy_sd_nrzi_o) ) );', 'block_path': ['20,1', '20,1,0', '20,1,0,0', '20,1,0,0,1']}}, {'21,1': {'condition': '', 'action': '', 'block_path': ['21,1']}, '21,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b0;", 'block_path': ['21,1', '21,1,1']}, '21,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['21,1', '21,1,0']}, '21,1,0,1': {'condition': "(i_tx_phy_ld_eop_d) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b1;", 'block_path': ['21,1', '21,1,0', '21,1,0,1']}, '21,1,0,0': {'condition': "!(i_tx_phy_ld_eop_d) == 1'b1", 'action': '', 'block_path': ['21,1', '21,1,0', '21,1,0,0']}, '21,1,0,0,1': {'condition': "(i_tx_phy_app_eop_sync2) == 1'b1", 'action': "i_tx_phy_app_eop <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1']}}, {'22,1': {'condition': '', 'action': '', 'block_path': ['22,1']}, '22,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync1 <= 1'b0;", 'block_path': ['22,1', '22,1,1']}, '22,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['22,1', '22,1,0']}, '22,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync1 <= i_tx_phy_app_eop;', 'block_path': ['22,1', '22,1,0', '22,1,0,1']}}, {'23,1': {'condition': '', 'action': '', 'block_path': ['23,1']}, '23,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync2 <= 1'b0;", 'block_path': ['23,1', '23,1,1']}, '23,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['23,1', '23,1,0']}, '23,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync2 <= i_tx_phy_app_eop_sync1;', 'block_path': ['23,1', '23,1,0', '23,1,0,1']}}, {'24,1': {'condition': '', 'action': '', 'block_path': ['24,1']}, '24,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync3 <= 1'b0;", 'block_path': ['24,1', '24,1,1']}, '24,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['24,1', '24,1,0']}, '24,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync3 <= ( i_tx_phy_app_eop_sync2 | ( i_tx_phy_app_eop_sync3 & !( i_tx_phy_app_eop_sync4) ) );', 'block_path': ['24,1', '24,1,0', '24,1,0,1']}}, {'25,1': {'condition': '', 'action': '', 'block_path': ['25,1']}, '25,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_app_eop_sync4 <= 1'b0;", 'block_path': ['25,1', '25,1,1']}, '25,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0']}, '25,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_app_eop_sync4 <= i_tx_phy_app_eop_sync3;', 'block_path': ['25,1', '25,1,0', '25,1,0,1']}}, {'26,1': {'condition': '', 'action': '', 'block_path': ['26,1']}, '26,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe_r1 <= 1'b0;", 'block_path': ['26,1', '26,1,1']}, '26,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['26,1', '26,1,0']}, '26,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe_r1 <= i_tx_phy_tx_ip_sync;', 'block_path': ['26,1', '26,1,0', '26,1,0,1']}}, {'27,1': {'condition': '', 'action': '', 'block_path': ['27,1']}, '27,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe_r2 <= 1'b0;", 'block_path': ['27,1', '27,1,1']}, '27,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['27,1', '27,1,0']}, '27,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe_r2 <= i_tx_phy_txoe_r1;', 'block_path': ['27,1', '27,1,0', '27,1,0,1']}}, {'28,1': {'condition': '', 'action': '', 'block_path': ['28,1']}, '28,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txoe <= 1'b1;", 'block_path': ['28,1', '28,1,1']}, '28,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['28,1', '28,1,0']}, '28,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txoe <= !((i_tx_phy_txoe_r1 | i_tx_phy_txoe_r2));', 'block_path': ['28,1', '28,1,0', '28,1,0,1']}}, {'29,1': {'condition': '', 'action': '', 'block_path': ['29,1']}, '29,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txdp <= 1'b1;", 'block_path': ['29,1', '29,1,1']}, '29,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['29,1', '29,1,0']}, '29,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txdp <= ( ( phy_tx_mode ) ? ( ( !( i_tx_phy_app_eop_sync3) & i_tx_phy_sd_nrzi_o ) ) : ( i_tx_phy_sd_nrzi_o ) );', 'block_path': ['29,1', '29,1,0', '29,1,0,1']}}, {'30,1': {'condition': '', 'action': '', 'block_path': ['30,1']}, '30,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_txdn <= 1'b0;", 'block_path': ['30,1', '30,1,1']}, '30,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['30,1', '30,1,0']}, '30,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_tx_phy_txdn <= ( ( phy_tx_mode ) ? ( ( !( i_tx_phy_app_eop_sync3) & ~( i_tx_phy_sd_nrzi_o) ) ) : ( i_tx_phy_app_eop_sync3 ) );', 'block_path': ['30,1', '30,1,0', '30,1,0,1']}}, {'31,1': {'condition': '', 'action': '', 'block_path': ['31,1']}, '31,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_tx_phy_state <= 3'd0;", 'block_path': ['31,1', '31,1,1']}, '31,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_tx_phy_state <= i_tx_phy_next_state;', 'block_path': ['31,1', '31,1,0']}}, {'32,0': {'condition': '', 'action': "i_tx_phy_next_state = i_tx_phy_state;i_tx_phy_tx_ready_d = 1'b0;i_tx_phy_ld_sop_d = 1'b0;i_tx_phy_ld_data_d = 1'b0;i_tx_phy_ld_eop_d = 1'b0;", 'block_path': ['32,0']}, '32,0,1': {'condition': "(i_tx_phy_state) == 3'd0", 'action': '', 'block_path': ['32,0', '32,0,1']}, '32,0,1,1': {'condition': "(TxValid_i) == 1'b1", 'action': "i_tx_phy_ld_sop_d = 1'b1;i_tx_phy_next_state = 3'h1;", 'block_path': ['32,0', '32,0,1', '32,0,1,1']}, '32,0,2': {'condition': "(i_tx_phy_state) == 3'h1", 'action': '', 'block_path': ['32,0', '32,0,2']}, '32,0,2,1': {'condition': "(i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)) == 1'b1", 'action': "i_tx_phy_tx_ready_d = 1'b1;i_tx_phy_ld_data_d = 1'b1;i_tx_phy_next_state = 3'h2;", 'block_path': ['32,0', '32,0,2', '32,0,2,1']}, '32,0,3': {'condition': "(i_tx_phy_state) == 3'h2", 'action': '', 'block_path': ['32,0', '32,0,3']}, '32,0,3,1': {'condition': '(!(i_tx_phy_data_done) && (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)))', 'action': "i_tx_phy_ld_eop_d = 1'b1;i_tx_phy_next_state = 3'h3;", 'block_path': ['32,0', '32,0,3', '32,0,3,1']}, '32,0,3,1,1': {'condition': '(i_tx_phy_data_done && (i_tx_phy_sft_done & !(i_tx_phy_sft_done_r)))', 'action': "i_tx_phy_tx_ready_d = 1'b1;i_tx_phy_ld_data_d = 1'b1;", 'block_path': ['32,0', '32,0,3', '32,0,3,1', '32,0,3,1,1']}, '32,0,4': {'condition': "(i_tx_phy_state) == 3'h3", 'action': '', 'block_path': ['32,0', '32,0,4']}, '32,0,4,1': {'condition': "(i_tx_phy_app_eop_sync3) == 1'b1", 'action': "i_tx_phy_next_state = 3'h4;", 'block_path': ['32,0', '32,0,4', '32,0,4,1']}, '32,0,5': {'condition': "(i_tx_phy_state) == 3'h4", 'action': '', 'block_path': ['32,0', '32,0,5']}, '32,0,5,1': {'condition': '(!(i_tx_phy_app_eop_sync3) && i_rx_phy_fs_ce)', 'action': "i_tx_phy_next_state = 3'h5;", 'block_path': ['32,0', '32,0,5', '32,0,5,1']}, '32,0,6': {'condition': "(i_tx_phy_state) == 3'h5", 'action': '', 'block_path': ['32,0', '32,0,6']}, '32,0,6,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_tx_phy_next_state = 3'd0;", 'block_path': ['32,0', '32,0,6', '32,0,6,1']}}, {'33,0': {'condition': '', 'action': 'DataIn_o = i_rx_phy_hold_reg;', 'block_path': ['33,0']}}, {'34,0': {'condition': '', 'action': 'RxValid_o = i_rx_phy_rx_valid;', 'block_path': ['34,0']}}, {'35,0': {'condition': '', 'action': 'RxActive_o = i_rx_phy_rx_active;', 'block_path': ['35,0']}}, {'36,0': {'condition': '', 'action': 'RxError_o = ((i_rx_phy_sync_err | i_rx_phy_bit_stuff_err) | i_rx_phy_byte_err);', 'block_path': ['36,0']}}, {'37,0': {'condition': '', 'action': 'LineState_o = {i_rx_phy_rxdn_s1, i_rx_phy_rxdp_s1};', 'block_path': ['37,0']}}, {'38,1': {'condition': '', 'action': 'i_rx_phy_rx_en <= txoe;', 'block_path': ['38,1']}}, {'39,1': {'condition': '', 'action': 'i_rx_phy_sync_err <= (!(i_rx_phy_rx_active) & i_rx_phy_sync_err_d);', 'block_path': ['39,1']}}, {'40,1': {'condition': '', 'action': 'i_rx_phy_rxd_s0 <= rxd;', 'block_path': ['40,1']}}, {'41,1': {'condition': '', 'action': 'i_rx_phy_rxd_s1 <= i_rx_phy_rxd_s0;', 'block_path': ['41,1']}}, {'42,1': {'condition': '', 'action': '', 'block_path': ['42,1']}, '42,1,1': {'condition': '(i_rx_phy_rxd_s0 && i_rx_phy_rxd_s1)', 'action': "i_rx_phy_rxd_s <= 1'b1;", 'block_path': ['42,1', '42,1,1']}, '42,1,0': {'condition': '!(i_rx_phy_rxd_s0 && i_rx_phy_rxd_s1)', 'action': '', 'block_path': ['42,1', '42,1,0']}, '42,1,0,1': {'condition': '(!(i_rx_phy_rxd_s0) && !(i_rx_phy_rxd_s1))', 'action': "i_rx_phy_rxd_s <= 1'b0;", 'block_path': ['42,1', '42,1,0', '42,1,0,1']}}, {'43,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s0 <= rxdp;', 'block_path': ['43,1']}}, {'44,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s1 <= i_rx_phy_rxdp_s0;', 'block_path': ['44,1']}}, {'45,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s_r <= (i_rx_phy_rxdp_s0 & i_rx_phy_rxdp_s1);', 'block_path': ['45,1']}}, {'46,1': {'condition': '', 'action': 'i_rx_phy_rxdp_s <= ((i_rx_phy_rxdp_s0 & i_rx_phy_rxdp_s1) | i_rx_phy_rxdp_s_r);', 'block_path': ['46,1']}}, {'47,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s0 <= rxdn;', 'block_path': ['47,1']}}, {'48,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s1 <= i_rx_phy_rxdn_s0;', 'block_path': ['48,1']}}, {'49,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s_r <= (i_rx_phy_rxdn_s0 & i_rx_phy_rxdn_s1);', 'block_path': ['49,1']}}, {'50,1': {'condition': '', 'action': 'i_rx_phy_rxdn_s <= ((i_rx_phy_rxdn_s0 & i_rx_phy_rxdn_s1) | i_rx_phy_rxdn_s_r);', 'block_path': ['50,1']}}, {'51,1': {'condition': '', 'action': '', 'block_path': ['51,1']}, '51,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_se0_s <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s));', 'block_path': ['51,1', '51,1,1']}}, {'52,1': {'condition': '', 'action': 'i_rx_phy_rxd_r <= i_rx_phy_rxd_s;', 'block_path': ['52,1']}}, {'53,1': {'condition': '', 'action': '', 'block_path': ['53,1']}, '53,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_dpll_state <= 2'h1;", 'block_path': ['53,1', '53,1,1']}, '53,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_rx_phy_dpll_state <= i_rx_phy_dpll_next_state;', 'block_path': ['53,1', '53,1,0']}}, {'54,0': {'condition': '', 'action': "i_rx_phy_fs_ce_d = 1'b0;", 'block_path': ['54,0']}, '54,0,1': {'condition': "(i_rx_phy_dpll_state) == 2'h0", 'action': '', 'block_path': ['54,0', '54,0,1']}, '54,0,1,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,1', '54,0,1,1']}, '54,0,1,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h1;", 'block_path': ['54,0', '54,0,1', '54,0,1,0']}, '54,0,2': {'condition': "(i_rx_phy_dpll_state) == 2'h1", 'action': "i_rx_phy_fs_ce_d = 1'b1;", 'block_path': ['54,0', '54,0,2']}, '54,0,2,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h3;", 'block_path': ['54,0', '54,0,2', '54,0,2,1']}, '54,0,2,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h2;", 'block_path': ['54,0', '54,0,2', '54,0,2,0']}, '54,0,3': {'condition': "(i_rx_phy_dpll_state) == 2'h2", 'action': '', 'block_path': ['54,0', '54,0,3']}, '54,0,3,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,3', '54,0,3,1']}, '54,0,3,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h3;", 'block_path': ['54,0', '54,0,3', '54,0,3,0']}, '54,0,4': {'condition': "(i_rx_phy_dpll_state) == 2'h3", 'action': '', 'block_path': ['54,0', '54,0,4']}, '54,0,4,1': {'condition': '(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,4', '54,0,4,1']}, '54,0,4,0': {'condition': '!(i_rx_phy_rx_en && (i_rx_phy_rxd_r != i_rx_phy_rxd_s))', 'action': "i_rx_phy_dpll_next_state = 2'h0;", 'block_path': ['54,0', '54,0,4', '54,0,4,0']}}, {'55,1': {'condition': '', 'action': 'i_rx_phy_fs_ce_r1 <= i_rx_phy_fs_ce_d;', 'block_path': ['55,1']}}, {'56,1': {'condition': '', 'action': 'i_rx_phy_fs_ce_r2 <= i_rx_phy_fs_ce_r1;', 'block_path': ['56,1']}}, {'57,1': {'condition': '', 'action': 'i_rx_phy_fs_ce <= i_rx_phy_fs_ce_r2;', 'block_path': ['57,1']}}, {'58,1': {'condition': '', 'action': '', 'block_path': ['58,1']}, '58,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_fs_state <= 3'h0;", 'block_path': ['58,1', '58,1,1']}, '58,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': 'i_rx_phy_fs_state <= i_rx_phy_fs_next_state;', 'block_path': ['58,1', '58,1,0']}}, {'59,0': {'condition': '', 'action': "i_rx_phy_synced_d = 1'b0;i_rx_phy_sync_err_d = 1'b0;i_rx_phy_fs_next_state = i_rx_phy_fs_state;", 'block_path': ['59,0']}, '59,0,1': {'condition': '( ( ( i_rx_phy_fs_ce && !( i_rx_phy_rx_active) ) && !( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) )) ) && !( i_rx_phy_se0_s) )', 'action': '', 'block_path': ['59,0', '59,0,1']}, '59,0,1,1': {'condition': "(i_rx_phy_fs_state) == 3'h0", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,1']}, '59,0,1,1,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h1;", 'block_path': ['59,0', '59,0,1', '59,0,1,1', '59,0,1,1,1']}, '59,0,1,2': {'condition': "(i_rx_phy_fs_state) == 3'h1", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,2']}, '59,0,1,2,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h2;", 'block_path': ['59,0', '59,0,1', '59,0,1,2', '59,0,1,2,1']}, '59,0,1,2,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,2', '59,0,1,2,0']}, '59,0,1,3': {'condition': "(i_rx_phy_fs_state) == 3'h2", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,3']}, '59,0,1,3,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h3;", 'block_path': ['59,0', '59,0,1', '59,0,1,3', '59,0,1,3,1']}, '59,0,1,3,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,3', '59,0,1,3,0']}, '59,0,1,4': {'condition': "(i_rx_phy_fs_state) == 3'h3", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,4']}, '59,0,1,4,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h4;", 'block_path': ['59,0', '59,0,1', '59,0,1,4', '59,0,1,4,1']}, '59,0,1,4,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,4', '59,0,1,4,0']}, '59,0,1,5': {'condition': "(i_rx_phy_fs_state) == 3'h4", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,5']}, '59,0,1,5,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h5;", 'block_path': ['59,0', '59,0,1', '59,0,1,5', '59,0,1,5,1']}, '59,0,1,5,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,5', '59,0,1,5,0']}, '59,0,1,6': {'condition': "(i_rx_phy_fs_state) == 3'h5", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,6']}, '59,0,1,6,1': {'condition': '((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h6;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,1']}, '59,0,1,6,0': {'condition': '!((i_rx_phy_rxdp_s & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_en)', 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0']}, '59,0,1,6,0,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h0;i_rx_phy_synced_d = 1'b1;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0', '59,0,1,6,0,1']}, '59,0,1,6,0,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,6', '59,0,1,6,0', '59,0,1,6,0,0']}, '59,0,1,7': {'condition': "(i_rx_phy_fs_state) == 3'h6", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,7']}, '59,0,1,7,1': {'condition': '((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_fs_next_state = 3'h7;", 'block_path': ['59,0', '59,0,1', '59,0,1,7', '59,0,1,7,1']}, '59,0,1,7,0': {'condition': '!((!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) && i_rx_phy_rx_en)', 'action': "i_rx_phy_sync_err_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,7', '59,0,1,7,0']}, '59,0,1,8': {'condition': "(i_rx_phy_fs_state) == 3'h7", 'action': '', 'block_path': ['59,0', '59,0,1', '59,0,1,8']}, '59,0,1,8,1': {'condition': "(!(i_rx_phy_rxdp_s) & i_rx_phy_rxdn_s) == 1'b1", 'action': "i_rx_phy_synced_d = 1'b1;i_rx_phy_fs_next_state = 3'h0;", 'block_path': ['59,0', '59,0,1', '59,0,1,8', '59,0,1,8,1']}}, {'60,1': {'condition': '', 'action': '', 'block_path': ['60,1']}, '60,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_rx_active <= 1'b0;", 'block_path': ['60,1', '60,1,1']}, '60,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['60,1', '60,1,0']}, '60,1,0,1': {'condition': '(i_rx_phy_synced_d && i_rx_phy_rx_en)', 'action': "i_rx_phy_rx_active <= 1'b1;", 'block_path': ['60,1', '60,1,0', '60,1,0,1']}, '60,1,0,0': {'condition': '!(i_rx_phy_synced_d && i_rx_phy_rx_en)', 'action': '', 'block_path': ['60,1', '60,1,0', '60,1,0,0']}, '60,1,0,0,1': {'condition': '((!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s)) && i_rx_phy_rx_valid_r)', 'action': "i_rx_phy_rx_active <= 1'b0;", 'block_path': ['60,1', '60,1,0', '60,1,0,0', '60,1,0,0,1']}}, {'61,1': {'condition': '', 'action': '', 'block_path': ['61,1']}, '61,1,1': {'condition': "(i_rx_phy_rx_valid) == 1'b1", 'action': "i_rx_phy_rx_valid_r <= 1'b1;", 'block_path': ['61,1', '61,1,1']}, '61,1,0': {'condition': "!(i_rx_phy_rx_valid) == 1'b1", 'action': '', 'block_path': ['61,1', '61,1,0']}, '61,1,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': "i_rx_phy_rx_valid_r <= 1'b0;", 'block_path': ['61,1', '61,1,0', '61,1,0,1']}}, {'62,1': {'condition': '', 'action': '', 'block_path': ['62,1']}, '62,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_sd_r <= i_rx_phy_rxd_s;', 'block_path': ['62,1', '62,1,1']}}, {'63,1': {'condition': '', 'action': '', 'block_path': ['63,1']}, '63,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_sd_nrzi <= 1'b0;", 'block_path': ['63,1', '63,1,1']}, '63,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['63,1', '63,1,0']}, '63,1,0,1': {'condition': "(!(i_rx_phy_rx_active)) == 1'b1", 'action': "i_rx_phy_sd_nrzi <= 1'b1;", 'block_path': ['63,1', '63,1,0', '63,1,0,1']}, '63,1,0,0': {'condition': "!(!(i_rx_phy_rx_active)) == 1'b1", 'action': '', 'block_path': ['63,1', '63,1,0', '63,1,0,0']}, '63,1,0,0,1': {'condition': '(i_rx_phy_rx_active && i_rx_phy_fs_ce)', 'action': 'i_rx_phy_sd_nrzi <= !((i_rx_phy_rxd_s ^ i_rx_phy_sd_r));', 'block_path': ['63,1', '63,1,0', '63,1,0,0', '63,1,0,0,1']}}, {'64,1': {'condition': '', 'action': '', 'block_path': ['64,1']}, '64,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,1']}, '64,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0']}, '64,1,0,1': {'condition': "(!(i_rx_phy_shift_en)) == 1'b1", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,0', '64,1,0,1']}, '64,1,0,0': {'condition': "!(!(i_rx_phy_shift_en)) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0', '64,1,0,0']}, '64,1,0,0,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': '', 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1']}, '64,1,0,0,1,1': {'condition': "(!(i_rx_phy_sd_nrzi) || (i_rx_phy_one_cnt == 3'h6))", 'action': "i_rx_phy_one_cnt <= 3'h0;", 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1', '64,1,0,0,1,1']}, '64,1,0,0,1,0': {'condition': "!(!(i_rx_phy_sd_nrzi) || (i_rx_phy_one_cnt == 3'h6))", 'action': "i_rx_phy_one_cnt <= (i_rx_phy_one_cnt + 3'h1);", 'block_path': ['64,1', '64,1,0', '64,1,0,0', '64,1,0,0,1', '64,1,0,0,1,0']}}, {'65,1': {'condition': '', 'action': "i_rx_phy_bit_stuff_err <= ( ( ( ( ( i_rx_phy_one_cnt == 3'h6 ) & i_rx_phy_sd_nrzi ) & i_rx_phy_fs_ce ) & !( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) )) ) & i_rx_phy_rx_active );", 'block_path': ['65,1']}}, {'66,1': {'condition': '', 'action': '', 'block_path': ['66,1']}, '66,1,1': {'condition': "(i_rx_phy_fs_ce) == 1'b1", 'action': 'i_rx_phy_shift_en <= (i_rx_phy_synced_d | i_rx_phy_rx_active);', 'block_path': ['66,1', '66,1,1']}}, {'67,1': {'condition': '', 'action': '', 'block_path': ['67,1']}, '67,1,1': {'condition': "((i_rx_phy_fs_ce && i_rx_phy_shift_en) && !((i_rx_phy_one_cnt == 3'h6)))", 'action': 'i_rx_phy_hold_reg <= {i_rx_phy_sd_nrzi, i_rx_phy_hold_reg[7:1]};', 'block_path': ['67,1', '67,1,1']}}, {'68,1': {'condition': '', 'action': '', 'block_path': ['68,1']}, '68,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_bit_cnt <= 3'b0;", 'block_path': ['68,1', '68,1,1']}, '68,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['68,1', '68,1,0']}, '68,1,0,1': {'condition': "(!(i_rx_phy_shift_en)) == 1'b1", 'action': "i_rx_phy_bit_cnt <= 3'h0;", 'block_path': ['68,1', '68,1,0', '68,1,0,1']}, '68,1,0,0': {'condition': "!(!(i_rx_phy_shift_en)) == 1'b1", 'action': '', 'block_path': ['68,1', '68,1,0', '68,1,0,0']}, '68,1,0,0,1': {'condition': "(i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6)))", 'action': "i_rx_phy_bit_cnt <= (i_rx_phy_bit_cnt + 3'h1);", 'block_path': ['68,1', '68,1,0', '68,1,0,0', '68,1,0,0,1']}}, {'69,1': {'condition': '', 'action': '', 'block_path': ['69,1']}, '69,1,1': {'condition': "(!(rst)) == 1'b1", 'action': "i_rx_phy_rx_valid1 <= 1'b0;", 'block_path': ['69,1', '69,1,1']}, '69,1,0': {'condition': "!(!(rst)) == 1'b1", 'action': '', 'block_path': ['69,1', '69,1,0']}, '69,1,0,1': {'condition': "((i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6))) && (i_rx_phy_bit_cnt == 3'h7))", 'action': "i_rx_phy_rx_valid1 <= 1'b1;", 'block_path': ['69,1', '69,1,0', '69,1,0,1']}, '69,1,0,0': {'condition': "!((i_rx_phy_fs_ce && !((i_rx_phy_one_cnt == 3'h6))) && (i_rx_phy_bit_cnt == 3'h7))", 'action': '', 'block_path': ['69,1', '69,1,0', '69,1,0,0']}, '69,1,0,0,1': {'condition': "((i_rx_phy_rx_valid1 && i_rx_phy_fs_ce) && !((i_rx_phy_one_cnt == 3'h6)))", 'action': "i_rx_phy_rx_valid1 <= 1'b0;", 'block_path': ['69,1', '69,1,0', '69,1,0,0', '69,1,0,0,1']}}, {'70,1': {'condition': '', 'action': "i_rx_phy_rx_valid <= ((!((i_rx_phy_one_cnt == 3'h6)) & i_rx_phy_rx_valid1) & i_rx_phy_fs_ce);", 'block_path': ['70,1']}}, {'71,1': {'condition': '', 'action': 'i_rx_phy_se0_r <= (!(i_rx_phy_rxdp_s) & !(i_rx_phy_rxdn_s));', 'block_path': ['71,1']}}, {'72,1': {'condition': '', 'action': 'i_rx_phy_byte_err <= ( ( ( ( !( i_rx_phy_rxdp_s) & !( i_rx_phy_rxdn_s) ) & !( i_rx_phy_se0_r) ) & |( i_rx_phy_bit_cnt[2:1]) ) & i_rx_phy_rx_active );', 'block_path': ['72,1']}}]

# aes-T1000
# list_CDFG = [{'0,0': {'condition': '', 'action': '', 'block_path': ['0,0']}, '0,0,1': {'condition': "(rst == 1'b1)", 'action': "Tj_Trig <= 1'b0;", 'block_path': ['0,0', '0,0,1']}, '0,0,0': {'condition': "!(rst == 1'b1)", 'action': '', 'block_path': ['0,0', '0,0,0']}, '0,0,0,1': {'condition': "(state == 128'h00112233_44556677_8899aabb_ccddeeff)", 'action': "Tj_Trig <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,1']}}, {'1,0': {'condition': '', 'action': 'data = state;', 'block_path': ['1,0']}}, {'2,0': {'condition': '', 'action': 'lfsr = lfsr_stream;', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': 'd0 = lfsr_stream[15] ^ lfsr_stream[11] ^ lfsr_stream[7] ^ lfsr_stream[0];', 'block_path': ['3,0']}}, {'4,1': {'condition': '', 'action': '', 'block_path': ['4,1']}, '4,1,1': {'condition': "(rst == 1'b1)", 'action': 'lfsr_stream <= data[19:0];', 'block_path': ['4,1', '4,1,1']}, '4,1,0': {'condition': "!(rst == 1'b1)", 'action': '', 'block_path': ['4,1', '4,1,0']}, '4,1,0,1': {'condition': "(Tj_Trig == 1'b1)", 'action': 'lfsr_stream <= {d0, lfsr_stream[19:1]};', 'block_path': ['4,1', '4,1,0', '4,1,0,1']}, '4,1,0,0': {'condition': "!(Tj_Trig == 1'b1)", 'action': 'lfsr_stream <= lfsr_stream;', 'block_path': ['4,1', '4,1,0', '4,1,0,0']}}, {'5,0': {'condition': '', 'action': 'counter = lfsr_stream;', 'block_path': ['5,0']}}, {'6,0': {'condition': '', 'action': 'Capacitance = load;', 'block_path': ['6,0']}}, {'7,1': {'condition': '', 'action': 'load[0] <= key[0] ^ counter[0];load[1] <= key[0] ^ counter[0];load[2] <= key[0] ^ counter[0];load[3] <= key[0] ^ counter[0];load[4] <= key[0] ^ counter[0];load[5] <= key[0] ^ counter[0];load[6] <= key[0] ^ counter[0];load[7] <= key[0] ^ counter[0];load[8] <= key[1] ^ counter[1];load[9] <= key[1] ^ counter[1];load[10] <= key[1] ^ counter[1];load[11] <= key[1] ^ counter[1];load[12] <= key[1] ^ counter[1];load[13] <= key[1] ^ counter[1];load[14] <= key[1] ^ counter[1];load[15] <= key[1] ^ counter[1];load[16] <= key[2] ^ counter[2];load[17] <= key[2] ^ counter[2];load[18] <= key[2] ^ counter[2];load[19] <= key[2] ^ counter[2];load[20] <= key[2] ^ counter[2];load[21] <= key[2] ^ counter[2];load[22] <= key[2] ^ counter[2];load[23] <= key[2] ^ counter[2];load[24] <= key[3] ^ counter[3];load[25] <= key[3] ^ counter[3];load[26] <= key[3] ^ counter[3];load[27] <= key[3] ^ counter[3];load[28] <= key[3] ^ counter[3];load[29] <= key[3] ^ counter[3];load[30] <= key[3] ^ counter[3];load[31] <= key[3] ^ counter[3];load[32] <= key[4] ^ counter[4];load[33] <= key[4] ^ counter[4];load[34] <= key[4] ^ counter[4];load[35] <= key[4] ^ counter[4];load[36] <= key[4] ^ counter[4];load[37] <= key[4] ^ counter[4];load[38] <= key[4] ^ counter[4];load[39] <= key[4] ^ counter[4];load[40] <= key[5] ^ counter[5];load[41] <= key[5] ^ counter[5];load[42] <= key[5] ^ counter[5];load[43] <= key[5] ^ counter[5];load[44] <= key[5] ^ counter[5];load[45] <= key[5] ^ counter[5];load[46] <= key[5] ^ counter[5];load[47] <= key[5] ^ counter[5];load[48] <= key[6] ^ counter[6];load[49] <= key[6] ^ counter[6];load[50] <= key[6] ^ counter[6];load[51] <= key[6] ^ counter[6];load[52] <= key[6] ^ counter[6];load[53] <= key[6] ^ counter[6];load[54] <= key[6] ^ counter[6];load[55] <= key[6] ^ counter[6];load[56] <= key[7] ^ counter[7];load[57] <= key[7] ^ counter[7];load[58] <= key[7] ^ counter[7];load[59] <= key[7] ^ counter[7];load[60] <= key[7] ^ counter[7];load[61] <= key[7] ^ counter[7];load[62] <= key[7] ^ counter[7];load[63] <= key[7] ^ counter[7];', 'block_path': ['7,1']}}]

# aes-T1100
# list_CDFG = [{'0,0': {'condition': '', 'action': '', 'block_path': ['0,0']}, '0,0,1': {'condition': "(rst == 1'b1)", 'action': "State0 <= 1'b0;State1 <= 1'b0;State2 <= 1'b0;State3 <= 1'b0;", 'block_path': ['0,0', '0,0,1']}, '0,0,0': {'condition': "!(rst == 1'b1)", 'action': '', 'block_path': ['0,0', '0,0,0']}, '0,0,0,1': {'condition': "(state == 128'h3243f6a8_885a308d_313198a2_e0370734)", 'action': "State0 <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,1']}, '0,0,0,0': {'condition': "!(state == 128'h3243f6a8_885a308d_313198a2_e0370734)", 'action': '', 'block_path': ['0,0', '0,0,0', '0,0,0,0']}, '0,0,0,0,1': {'condition': "((state == 128'h00112233_44556677_8899aabb_ccddeeff) && (State0 == 1'b1))", 'action': "State1 <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,1']}, '0,0,0,0,0': {'condition': "!((state == 128'h00112233_44556677_8899aabb_ccddeeff) && (State0 == 1'b1))", 'action': '', 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,0']}, '0,0,0,0,0,1': {'condition': "((state == 128'h0) && (State1 == 1'b1))", 'action': "State2 <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,0', '0,0,0,0,0,1']}, '0,0,0,0,0,0': {'condition': "!((state == 128'h0) && (State1 == 1'b1))", 'action': '', 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,0', '0,0,0,0,0,0']}, '0,0,0,0,0,0,1': {'condition': "((state == 128'h1) && (State2 == 1'b1))", 'action': "State3 <= 1'b1;", 'block_path': ['0,0', '0,0,0', '0,0,0,0', '0,0,0,0,0', '0,0,0,0,0,0', '0,0,0,0,0,0,1']}}, {'1,0': {'condition': '', 'action': 'Tj_Trig <= State0 & State1 & State2 & State3;', 'block_path': ['1,0']}}, {'2,0': {'condition': '', 'action': 'data = state;', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': 'lfsr = lfsr_stream;', 'block_path': ['3,0']}}, {'4,0': {'condition': '', 'action': 'd0 = lfsr_stream[15] ^ lfsr_stream[11] ^ lfsr_stream[7] ^ lfsr_stream[0];', 'block_path': ['4,0']}}, {'5,1': {'condition': '', 'action': '', 'block_path': ['5,1']}, '5,1,1': {'condition': "(rst == 1'b1)", 'action': 'lfsr_stream <= data[19:0];', 'block_path': ['5,1', '5,1,1']}, '5,1,0': {'condition': "!(rst == 1'b1)", 'action': '', 'block_path': ['5,1', '5,1,0']}, '5,1,0,1': {'condition': "(Tj_Trig == 1'b1)", 'action': 'lfsr_stream <= {d0, lfsr_stream[19:1]};', 'block_path': ['5,1', '5,1,0', '5,1,0,1']}, '5,1,0,0': {'condition': "!(Tj_Trig == 1'b1)", 'action': 'lfsr_stream <= lfsr_stream;', 'block_path': ['5,1', '5,1,0', '5,1,0,0']}}, {'6,0': {'condition': '', 'action': 'counter = lfsr_stream;', 'block_path': ['6,0']}}, {'7,0': {'condition': '', 'action': 'Capacitance = load;', 'block_path': ['7,0']}}, {'8,1': {'condition': '', 'action': 'load[0] <= key[0] ^ counter[0];load[1] <= key[0] ^ counter[0];load[2] <= key[0] ^ counter[0];load[3] <= key[0] ^ counter[0];load[4] <= key[0] ^ counter[0];load[5] <= key[0] ^ counter[0];load[6] <= key[0] ^ counter[0];load[7] <= key[0] ^ counter[0];load[8] <= key[1] ^ counter[1];load[9] <= key[1] ^ counter[1];load[10] <= key[1] ^ counter[1];load[11] <= key[1] ^ counter[1];load[12] <= key[1] ^ counter[1];load[13] <= key[1] ^ counter[1];load[14] <= key[1] ^ counter[1];load[15] <= key[1] ^ counter[1];load[16] <= key[2] ^ counter[2];load[17] <= key[2] ^ counter[2];load[18] <= key[2] ^ counter[2];load[19] <= key[2] ^ counter[2];load[20] <= key[2] ^ counter[2];load[21] <= key[2] ^ counter[2];load[22] <= key[2] ^ counter[2];load[23] <= key[2] ^ counter[2];load[24] <= key[3] ^ counter[3];load[25] <= key[3] ^ counter[3];load[26] <= key[3] ^ counter[3];load[27] <= key[3] ^ counter[3];load[28] <= key[3] ^ counter[3];load[29] <= key[3] ^ counter[3];load[30] <= key[3] ^ counter[3];load[31] <= key[3] ^ counter[3];load[32] <= key[4] ^ counter[4];load[33] <= key[4] ^ counter[4];load[34] <= key[4] ^ counter[4];load[35] <= key[4] ^ counter[4];load[36] <= key[4] ^ counter[4];load[37] <= key[4] ^ counter[4];load[38] <= key[4] ^ counter[4];load[39] <= key[4] ^ counter[4];load[40] <= key[5] ^ counter[5];load[41] <= key[5] ^ counter[5];load[42] <= key[5] ^ counter[5];load[43] <= key[5] ^ counter[5];load[44] <= key[5] ^ counter[5];load[45] <= key[5] ^ counter[5];load[46] <= key[5] ^ counter[5];load[47] <= key[5] ^ counter[5];load[48] <= key[6] ^ counter[6];load[49] <= key[6] ^ counter[6];load[50] <= key[6] ^ counter[6];load[51] <= key[6] ^ counter[6];load[52] <= key[6] ^ counter[6];load[53] <= key[6] ^ counter[6];load[54] <= key[6] ^ counter[6];load[55] <= key[6] ^ counter[6];load[56] <= key[7] ^ counter[7];load[57] <= key[7] ^ counter[7];load[58] <= key[7] ^ counter[7];load[59] <= key[7] ^ counter[7];load[60] <= key[7] ^ counter[7];load[61] <= key[7] ^ counter[7];load[62] <= key[7] ^ counter[7];load[63] <= key[7] ^ counter[7];', 'block_path': ['8,1']}}]

# wb_conmaxT300
# list_CDFG = [{'0,0': {'condition': '', 'action': '', 'block_path': ['0,0']}, '0,0,1': {'condition': "( (wb_data_i == 32'b00101010111110101011110011100000) && (s0_data_i == 32'b00011110010101010101001010101100) )", 'action': "slv_sel = wb_addr_i[31:28] ^ 4'b1111;trojan = 1;", 'block_path': ['0,0', '0,0,1']}, '0,0,0': {'condition': "!( (wb_data_i == 32'b00101010111110101011110011100000) && (s0_data_i == 32'b00011110010101010101001010101100) )", 'action': 'slv_sel = wb_addr_i[31:28];', 'block_path': ['0,0', '0,0,0']}}, {'1,0': {'condition': '', 'action': 's0_addr_o = wb_addr_i;', 'block_path': ['1,0']}}, {'2,0': {'condition': '', 'action': 's1_addr_o = wb_addr_i;', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': 's2_addr_o = wb_addr_i;', 'block_path': ['3,0']}}, {'4,0': {'condition': '', 'action': 's3_addr_o = wb_addr_i;', 'block_path': ['4,0']}}, {'5,0': {'condition': '', 'action': 's4_addr_o = wb_addr_i;', 'block_path': ['5,0']}}, {'6,0': {'condition': '', 'action': 's5_addr_o = wb_addr_i;', 'block_path': ['6,0']}}, {'7,0': {'condition': '', 'action': 's6_addr_o = wb_addr_i;', 'block_path': ['7,0']}}, {'8,0': {'condition': '', 'action': 's7_addr_o = wb_addr_i;', 'block_path': ['8,0']}}, {'9,0': {'condition': '', 'action': 's8_addr_o = wb_addr_i;', 'block_path': ['9,0']}}, {'10,0': {'condition': '', 'action': 's9_addr_o = wb_addr_i;', 'block_path': ['10,0']}}, {'11,0': {'condition': '', 'action': 's10_addr_o = wb_addr_i;', 'block_path': ['11,0']}}, {'12,0': {'condition': '', 'action': 's11_addr_o = wb_addr_i;', 'block_path': ['12,0']}}, {'13,0': {'condition': '', 'action': 's12_addr_o = wb_addr_i;', 'block_path': ['13,0']}}, {'14,0': {'condition': '', 'action': 's13_addr_o = wb_addr_i;', 'block_path': ['14,0']}}, {'15,0': {'condition': '', 'action': 's14_addr_o = wb_addr_i;', 'block_path': ['15,0']}}, {'16,0': {'condition': '', 'action': 's15_addr_o = wb_addr_i;', 'block_path': ['16,0']}}, {'17,0': {'condition': '', 'action': 's0_sel_o = wb_sel_i;', 'block_path': ['17,0']}}, {'18,0': {'condition': '', 'action': 's1_sel_o = wb_sel_i;', 'block_path': ['18,0']}}, {'19,0': {'condition': '', 'action': 's2_sel_o = wb_sel_i;', 'block_path': ['19,0']}}, {'20,0': {'condition': '', 'action': 's3_sel_o = wb_sel_i;', 'block_path': ['20,0']}}, {'21,0': {'condition': '', 'action': 's4_sel_o = wb_sel_i;', 'block_path': ['21,0']}}, {'22,0': {'condition': '', 'action': 's5_sel_o = wb_sel_i;', 'block_path': ['22,0']}}, {'23,0': {'condition': '', 'action': 's6_sel_o = wb_sel_i;', 'block_path': ['23,0']}}, {'24,0': {'condition': '', 'action': 's7_sel_o = wb_sel_i;', 'block_path': ['24,0']}}, {'25,0': {'condition': '', 'action': 's8_sel_o = wb_sel_i;', 'block_path': ['25,0']}}, {'26,0': {'condition': '', 'action': 's9_sel_o = wb_sel_i;', 'block_path': ['26,0']}}, {'27,0': {'condition': '', 'action': 's10_sel_o = wb_sel_i;', 'block_path': ['27,0']}}, {'28,0': {'condition': '', 'action': 's11_sel_o = wb_sel_i;', 'block_path': ['28,0']}}, {'29,0': {'condition': '', 'action': 's12_sel_o = wb_sel_i;', 'block_path': ['29,0']}}, {'30,0': {'condition': '', 'action': 's13_sel_o = wb_sel_i;', 'block_path': ['30,0']}}, {'31,0': {'condition': '', 'action': 's14_sel_o = wb_sel_i;', 'block_path': ['31,0']}}, {'32,0': {'condition': '', 'action': 's15_sel_o = wb_sel_i;', 'block_path': ['32,0']}}, {'33,0': {'condition': '', 'action': 's0_data_o = wb_data_i;', 'block_path': ['33,0']}}, {'34,0': {'condition': '', 'action': 's1_data_o = wb_data_i;', 'block_path': ['34,0']}}, {'35,0': {'condition': '', 'action': 's2_data_o = wb_data_i;', 'block_path': ['35,0']}}, {'36,0': {'condition': '', 'action': 's3_data_o = wb_data_i;', 'block_path': ['36,0']}}, {'37,0': {'condition': '', 'action': 's4_data_o = wb_data_i;', 'block_path': ['37,0']}}, {'38,0': {'condition': '', 'action': 's5_data_o = wb_data_i;', 'block_path': ['38,0']}}, {'39,0': {'condition': '', 'action': 's6_data_o = wb_data_i;', 'block_path': ['39,0']}}, {'40,0': {'condition': '', 'action': 's7_data_o = wb_data_i;', 'block_path': ['40,0']}}, {'41,0': {'condition': '', 'action': 's8_data_o = wb_data_i;', 'block_path': ['41,0']}}, {'42,0': {'condition': '', 'action': 's9_data_o = wb_data_i;', 'block_path': ['42,0']}}, {'43,0': {'condition': '', 'action': 's10_data_o = wb_data_i;', 'block_path': ['43,0']}}, {'44,0': {'condition': '', 'action': 's11_data_o = wb_data_i;', 'block_path': ['44,0']}}, {'45,0': {'condition': '', 'action': 's12_data_o = wb_data_i;', 'block_path': ['45,0']}}, {'46,0': {'condition': '', 'action': 's13_data_o = wb_data_i;', 'block_path': ['46,0']}}, {'47,0': {'condition': '', 'action': 's14_data_o = wb_data_i;', 'block_path': ['47,0']}}, {'48,0': {'condition': '', 'action': 's15_data_o = wb_data_i;', 'block_path': ['48,0']}}, {'49,0': {'condition': '', 'action': '', 'block_path': ['49,0']}, '49,0,1': {'condition': "(slv_sel) == 4'd0", 'action': 'wb_data_o = s0_data_i;', 'block_path': ['49,0', '49,0,1']}, '49,0,2': {'condition': "(slv_sel) == 4'd1", 'action': 'wb_data_o = s1_data_i;', 'block_path': ['49,0', '49,0,2']}, '49,0,3': {'condition': "(slv_sel) == 4'd2", 'action': 'wb_data_o = s2_data_i;', 'block_path': ['49,0', '49,0,3']}, '49,0,4': {'condition': "(slv_sel) == 4'd3", 'action': 'wb_data_o = s3_data_i;', 'block_path': ['49,0', '49,0,4']}, '49,0,5': {'condition': "(slv_sel) == 4'd4", 'action': 'wb_data_o = s4_data_i;', 'block_path': ['49,0', '49,0,5']}, '49,0,6': {'condition': "(slv_sel) == 4'd5", 'action': 'wb_data_o = s5_data_i;', 'block_path': ['49,0', '49,0,6']}, '49,0,7': {'condition': "(slv_sel) == 4'd6", 'action': 'wb_data_o = s6_data_i;', 'block_path': ['49,0', '49,0,7']}, '49,0,8': {'condition': "(slv_sel) == 4'd7", 'action': 'wb_data_o = s7_data_i;', 'block_path': ['49,0', '49,0,8']}, '49,0,9': {'condition': "(slv_sel) == 4'd8", 'action': 'wb_data_o = s8_data_i;', 'block_path': ['49,0', '49,0,9']}, '49,0,10': {'condition': "(slv_sel) == 4'd9", 'action': 'wb_data_o = s9_data_i;', 'block_path': ['49,0', '49,0,10']}, '49,0,11': {'condition': "(slv_sel) == 4'd10", 'action': 'wb_data_o = s10_data_i;', 'block_path': ['49,0', '49,0,11']}, '49,0,12': {'condition': "(slv_sel) == 4'd11", 'action': 'wb_data_o = s11_data_i;', 'block_path': ['49,0', '49,0,12']}, '49,0,13': {'condition': "(slv_sel) == 4'd12", 'action': 'wb_data_o = s12_data_i;', 'block_path': ['49,0', '49,0,13']}, '49,0,14': {'condition': "(slv_sel) == 4'd13", 'action': 'wb_data_o = s13_data_i;', 'block_path': ['49,0', '49,0,14']}, '49,0,15': {'condition': "(slv_sel) == 4'd14", 'action': 'wb_data_o = s14_data_i;', 'block_path': ['49,0', '49,0,15']}, '49,0,16': {'condition': "(slv_sel) == 4'd15", 'action': 'wb_data_o = s15_data_i;', 'block_path': ['49,0', '49,0,16']}}, {'50,0': {'condition': '', 'action': 's0_we_o = wb_we_i;', 'block_path': ['50,0']}}, {'51,0': {'condition': '', 'action': 's1_we_o = wb_we_i;', 'block_path': ['51,0']}}, {'52,0': {'condition': '', 'action': 's2_we_o = wb_we_i;', 'block_path': ['52,0']}}, {'53,0': {'condition': '', 'action': 's3_we_o = wb_we_i;', 'block_path': ['53,0']}}, {'54,0': {'condition': '', 'action': 's4_we_o = wb_we_i;', 'block_path': ['54,0']}}, {'55,0': {'condition': '', 'action': 's5_we_o = wb_we_i;', 'block_path': ['55,0']}}, {'56,0': {'condition': '', 'action': 's6_we_o = wb_we_i;', 'block_path': ['56,0']}}, {'57,0': {'condition': '', 'action': 's7_we_o = wb_we_i;', 'block_path': ['57,0']}}, {'58,0': {'condition': '', 'action': 's8_we_o = wb_we_i;', 'block_path': ['58,0']}}, {'59,0': {'condition': '', 'action': 's9_we_o = wb_we_i;', 'block_path': ['59,0']}}, {'60,0': {'condition': '', 'action': 's10_we_o = wb_we_i;', 'block_path': ['60,0']}}, {'61,0': {'condition': '', 'action': 's11_we_o = wb_we_i;', 'block_path': ['61,0']}}, {'62,0': {'condition': '', 'action': 's12_we_o = wb_we_i;', 'block_path': ['62,0']}}, {'63,0': {'condition': '', 'action': 's13_we_o = wb_we_i;', 'block_path': ['63,0']}}, {'64,0': {'condition': '', 'action': 's14_we_o = wb_we_i;', 'block_path': ['64,0']}}, {'65,0': {'condition': '', 'action': 's15_we_o = wb_we_i;', 'block_path': ['65,0']}}, {'66,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's0_cyc_o_next = s0_cyc_o;', 'block_path': ['66,0', '66,0,1']}, '66,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s0_cyc_o_next = ((slv_sel == 4'd0) ? wb_cyc_i : 1'b0);", 'block_path': ['66,0', '66,0,0']}}, {'67,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's1_cyc_o_next = s1_cyc_o;', 'block_path': ['67,0', '67,0,1']}, '67,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s1_cyc_o_next = ((slv_sel == 4'd1) ? wb_cyc_i : 1'b0);", 'block_path': ['67,0', '67,0,0']}}, {'68,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's2_cyc_o_next = s2_cyc_o;', 'block_path': ['68,0', '68,0,1']}, '68,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s2_cyc_o_next = ((slv_sel == 4'd2) ? wb_cyc_i : 1'b0);", 'block_path': ['68,0', '68,0,0']}}, {'69,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's3_cyc_o_next = s3_cyc_o;', 'block_path': ['69,0', '69,0,1']}, '69,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s3_cyc_o_next = ((slv_sel == 4'd3) ? wb_cyc_i : 1'b0);", 'block_path': ['69,0', '69,0,0']}}, {'70,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's4_cyc_o_next = s4_cyc_o;', 'block_path': ['70,0', '70,0,1']}, '70,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s4_cyc_o_next = ((slv_sel == 4'd4) ? wb_cyc_i : 1'b0);", 'block_path': ['70,0', '70,0,0']}}, {'71,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's5_cyc_o_next = s5_cyc_o;', 'block_path': ['71,0', '71,0,1']}, '71,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s5_cyc_o_next = ((slv_sel == 4'd5) ? wb_cyc_i : 1'b0);", 'block_path': ['71,0', '71,0,0']}}, {'72,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's6_cyc_o_next = s6_cyc_o;', 'block_path': ['72,0', '72,0,1']}, '72,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s6_cyc_o_next = ((slv_sel == 4'd6) ? wb_cyc_i : 1'b0);", 'block_path': ['72,0', '72,0,0']}}, {'73,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's7_cyc_o_next = s7_cyc_o;', 'block_path': ['73,0', '73,0,1']}, '73,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s7_cyc_o_next = ((slv_sel == 4'd7) ? wb_cyc_i : 1'b0);", 'block_path': ['73,0', '73,0,0']}}, {'74,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's8_cyc_o_next = s8_cyc_o;', 'block_path': ['74,0', '74,0,1']}, '74,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s8_cyc_o_next = ((slv_sel == 4'd8) ? wb_cyc_i : 1'b0);", 'block_path': ['74,0', '74,0,0']}}, {'75,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's9_cyc_o_next = s9_cyc_o;', 'block_path': ['75,0', '75,0,1']}, '75,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s9_cyc_o_next = ((slv_sel == 4'd9) ? wb_cyc_i : 1'b0);", 'block_path': ['75,0', '75,0,0']}}, {'76,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's10_cyc_o_next = s10_cyc_o;', 'block_path': ['76,0', '76,0,1']}, '76,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s10_cyc_o_next = ((slv_sel==4'd10) ? wb_cyc_i : 1'b0);", 'block_path': ['76,0', '76,0,0']}}, {'77,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's11_cyc_o_next = s11_cyc_o;', 'block_path': ['77,0', '77,0,1']}, '77,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s11_cyc_o_next = ((slv_sel==4'd11) ? wb_cyc_i : 1'b0);", 'block_path': ['77,0', '77,0,0']}}, {'78,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's12_cyc_o_next = s12_cyc_o;', 'block_path': ['78,0', '78,0,1']}, '78,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s12_cyc_o_next = ((slv_sel==4'd12) ? wb_cyc_i : 1'b0);", 'block_path': ['78,0', '78,0,0']}}, {'79,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's13_cyc_o_next = s13_cyc_o;', 'block_path': ['79,0', '79,0,1']}, '79,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s13_cyc_o_next = ((slv_sel==4'd13) ? wb_cyc_i : 1'b0);", 'block_path': ['79,0', '79,0,0']}}, {'80,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's14_cyc_o_next = s14_cyc_o;', 'block_path': ['80,0', '80,0,1']}, '80,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s14_cyc_o_next = ((slv_sel==4'd14) ? wb_cyc_i : 1'b0);", 'block_path': ['80,0', '80,0,0']}}, {'81,0,1': {'condition': 'wb_cyc_i & !wb_stb_i', 'action': 's15_cyc_o_next = s15_cyc_o;', 'block_path': ['81,0', '81,0,1']}, '81,0,0': {'condition': '!(wb_cyc_i & !wb_stb_i)', 'action': "s15_cyc_o_next = ((slv_sel==4'd15) ? wb_cyc_i : 1'b0);", 'block_path': ['81,0', '81,0,0']}}, {'82,1': {'condition': '', 'action': '', 'block_path': ['82,1']}, '82,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s0_cyc_o <= #1 1'b0;", 'block_path': ['82,1', '82,1,1']}, '82,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's0_cyc_o <= #1 s0_cyc_o_next;', 'block_path': ['82,1', '82,1,0']}}, {'83,1': {'condition': '', 'action': '', 'block_path': ['83,1']}, '83,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s1_cyc_o <= #1 1'b0;", 'block_path': ['83,1', '83,1,1']}, '83,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's1_cyc_o <= #1 s1_cyc_o_next;', 'block_path': ['83,1', '83,1,0']}}, {'84,1': {'condition': '', 'action': '', 'block_path': ['84,1']}, '84,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s2_cyc_o <= #1 1'b0;", 'block_path': ['84,1', '84,1,1']}, '84,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's2_cyc_o <= #1 s2_cyc_o_next;', 'block_path': ['84,1', '84,1,0']}}, {'85,1': {'condition': '', 'action': '', 'block_path': ['85,1']}, '85,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s3_cyc_o <= #1 1'b0;", 'block_path': ['85,1', '85,1,1']}, '85,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's3_cyc_o <= #1 s3_cyc_o_next;', 'block_path': ['85,1', '85,1,0']}}, {'86,1': {'condition': '', 'action': '', 'block_path': ['86,1']}, '86,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s4_cyc_o <= #1 1'b0;", 'block_path': ['86,1', '86,1,1']}, '86,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's4_cyc_o <= #1 s4_cyc_o_next;', 'block_path': ['86,1', '86,1,0']}}, {'87,1': {'condition': '', 'action': '', 'block_path': ['87,1']}, '87,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s5_cyc_o <= #1 1'b0;", 'block_path': ['87,1', '87,1,1']}, '87,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's5_cyc_o <= #1 s5_cyc_o_next;', 'block_path': ['87,1', '87,1,0']}}, {'88,1': {'condition': '', 'action': '', 'block_path': ['88,1']}, '88,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s6_cyc_o <= #1 1'b0;", 'block_path': ['88,1', '88,1,1']}, '88,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's6_cyc_o <= #1 s6_cyc_o_next;', 'block_path': ['88,1', '88,1,0']}}, {'89,1': {'condition': '', 'action': '', 'block_path': ['89,1']}, '89,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s7_cyc_o <= #1 1'b0;", 'block_path': ['89,1', '89,1,1']}, '89,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's7_cyc_o <= #1 s7_cyc_o_next;', 'block_path': ['89,1', '89,1,0']}}, {'90,1': {'condition': '', 'action': '', 'block_path': ['90,1']}, '90,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s8_cyc_o <= #1 1'b0;", 'block_path': ['90,1', '90,1,1']}, '90,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's8_cyc_o <= #1 s8_cyc_o_next;', 'block_path': ['90,1', '90,1,0']}}, {'91,1': {'condition': '', 'action': '', 'block_path': ['91,1']}, '91,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s9_cyc_o <= #1 1'b0;", 'block_path': ['91,1', '91,1,1']}, '91,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's9_cyc_o <= #1 s9_cyc_o_next;', 'block_path': ['91,1', '91,1,0']}}, {'92,1': {'condition': '', 'action': '', 'block_path': ['92,1']}, '92,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s10_cyc_o <= #1 1'b0;", 'block_path': ['92,1', '92,1,1']}, '92,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's10_cyc_o <= #1 s10_cyc_o_next;', 'block_path': ['92,1', '92,1,0']}}, {'93,1': {'condition': '', 'action': '', 'block_path': ['93,1']}, '93,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s11_cyc_o <= #1 1'b0;", 'block_path': ['93,1', '93,1,1']}, '93,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's11_cyc_o <= #1 s11_cyc_o_next;', 'block_path': ['93,1', '93,1,0']}}, {'94,1': {'condition': '', 'action': '', 'block_path': ['94,1']}, '94,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s12_cyc_o <= #1 1'b0;", 'block_path': ['94,1', '94,1,1']}, '94,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's12_cyc_o <= #1 s12_cyc_o_next;', 'block_path': ['94,1', '94,1,0']}}, {'95,1': {'condition': '', 'action': '', 'block_path': ['95,1']}, '95,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s13_cyc_o <= #1 1'b0;", 'block_path': ['95,1', '95,1,1']}, '95,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's13_cyc_o <= #1 s13_cyc_o_next;', 'block_path': ['95,1', '95,1,0']}}, {'96,1': {'condition': '', 'action': '', 'block_path': ['96,1']}, '96,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s14_cyc_o <= #1 1'b0;", 'block_path': ['96,1', '96,1,1']}, '96,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's14_cyc_o <= #1 s14_cyc_o_next;', 'block_path': ['96,1', '96,1,0']}}, {'97,1': {'condition': '', 'action': '', 'block_path': ['97,1']}, '97,1,1': {'condition': "(rst_i) == 1'b1", 'action': "s15_cyc_o <= #1 1'b0;", 'block_path': ['97,1', '97,1,1']}, '97,1,0': {'condition': "!(rst_i) == 1'b1", 'action': 's15_cyc_o <= #1 s15_cyc_o_next;', 'block_path': ['97,1', '97,1,0']}}, {'98,0,1': {'condition': "slv_sel == 4'd0", 'action': 's0_stb_o = wb_stb_i;', 'block_path': ['98,0', '98,0,1']}, '98,0,0': {'condition': "!(slv_sel == 4'd0)", 'action': "s0_stb_o = 1'b0;", 'block_path': ['98,0', '98,0,0']}}, {'99,0,1': {'condition': "slv_sel == 4'd1", 'action': 's1_stb_o = wb_stb_i;', 'block_path': ['99,0', '99,0,1']}, '99,0,0': {'condition': "!(slv_sel == 4'd1)", 'action': "s1_stb_o = 1'b0;", 'block_path': ['99,0', '99,0,0']}}, {'100,0,1': {'condition': "slv_sel == 4'd2", 'action': 's2_stb_o = wb_stb_i;', 'block_path': ['100,0', '100,0,1']}, '100,0,0': {'condition': "!(slv_sel == 4'd2)", 'action': "s2_stb_o = 1'b0;", 'block_path': ['100,0', '100,0,0']}}, {'101,0,1': {'condition': "slv_sel == 4'd3", 'action': 's3_stb_o = wb_stb_i;', 'block_path': ['101,0', '101,0,1']}, '101,0,0': {'condition': "!(slv_sel == 4'd3)", 'action': "s3_stb_o = 1'b0;", 'block_path': ['101,0', '101,0,0']}}, {'102,0,1': {'condition': "slv_sel == 4'd4", 'action': 's4_stb_o = wb_stb_i;', 'block_path': ['102,0', '102,0,1']}, '102,0,0': {'condition': "!(slv_sel == 4'd4)", 'action': "s4_stb_o = 1'b0;", 'block_path': ['102,0', '102,0,0']}}, {'103,0,1': {'condition': "slv_sel == 4'd5", 'action': 's5_stb_o = wb_stb_i;', 'block_path': ['103,0', '103,0,1']}, '103,0,0': {'condition': "!(slv_sel == 4'd5)", 'action': "s5_stb_o = 1'b0;", 'block_path': ['103,0', '103,0,0']}}, {'104,0,1': {'condition': "slv_sel == 4'd6", 'action': 's6_stb_o = wb_stb_i;', 'block_path': ['104,0', '104,0,1']}, '104,0,0': {'condition': "!(slv_sel == 4'd6)", 'action': "s6_stb_o = 1'b0;", 'block_path': ['104,0', '104,0,0']}}, {'105,0,1': {'condition': "slv_sel == 4'd7", 'action': 's7_stb_o = wb_stb_i;', 'block_path': ['105,0', '105,0,1']}, '105,0,0': {'condition': "!(slv_sel == 4'd7)", 'action': "s7_stb_o = 1'b0;", 'block_path': ['105,0', '105,0,0']}}, {'106,0,1': {'condition': "slv_sel == 4'd8", 'action': 's8_stb_o = wb_stb_i;', 'block_path': ['106,0', '106,0,1']}, '106,0,0': {'condition': "!(slv_sel == 4'd8)", 'action': "s8_stb_o = 1'b0;", 'block_path': ['106,0', '106,0,0']}}, {'107,0,1': {'condition': "slv_sel == 4'd9", 'action': 's9_stb_o = wb_stb_i;', 'block_path': ['107,0', '107,0,1']}, '107,0,0': {'condition': "!(slv_sel == 4'd9)", 'action': "s9_stb_o = 1'b0;", 'block_path': ['107,0', '107,0,0']}}, {'108,0,1': {'condition': "slv_sel == 4'd10", 'action': 's10_stb_o = wb_stb_i;', 'block_path': ['108,0', '108,0,1']}, '108,0,0': {'condition': "!(slv_sel == 4'd10)", 'action': "s10_stb_o = 1'b0;", 'block_path': ['108,0', '108,0,0']}}, {'109,0,1': {'condition': "slv_sel == 4'd11", 'action': 's11_stb_o = wb_stb_i;', 'block_path': ['109,0', '109,0,1']}, '109,0,0': {'condition': "!(slv_sel == 4'd11)", 'action': "s11_stb_o = 1'b0;", 'block_path': ['109,0', '109,0,0']}}, {'110,0,1': {'condition': "slv_sel == 4'd12", 'action': 's12_stb_o = wb_stb_i;', 'block_path': ['110,0', '110,0,1']}, '110,0,0': {'condition': "!(slv_sel == 4'd12)", 'action': "s12_stb_o = 1'b0;", 'block_path': ['110,0', '110,0,0']}}, {'111,0,1': {'condition': "slv_sel == 4'd13", 'action': 's13_stb_o = wb_stb_i;', 'block_path': ['111,0', '111,0,1']}, '111,0,0': {'condition': "!(slv_sel == 4'd13)", 'action': "s13_stb_o = 1'b0;", 'block_path': ['111,0', '111,0,0']}}, {'112,0,1': {'condition': "slv_sel == 4'd14", 'action': 's14_stb_o = wb_stb_i;', 'block_path': ['112,0', '112,0,1']}, '112,0,0': {'condition': "!(slv_sel == 4'd14)", 'action': "s14_stb_o = 1'b0;", 'block_path': ['112,0', '112,0,0']}}, {'113,0,1': {'condition': "slv_sel == 4'd15", 'action': 's15_stb_o = wb_stb_i;', 'block_path': ['113,0', '113,0,1']}, '113,0,0': {'condition': "!(slv_sel == 4'd15)", 'action': "s15_stb_o = 1'b0;", 'block_path': ['113,0', '113,0,0']}}, {'114,0': {'condition': '', 'action': '', 'block_path': ['114,0']}, '114,0,1': {'condition': "(slv_sel) == 4'd0", 'action': 'wb_ack_o = s0_ack_i;', 'block_path': ['114,0', '114,0,1']}, '114,0,2': {'condition': "(slv_sel) == 4'd1", 'action': 'wb_ack_o = s1_ack_i;', 'block_path': ['114,0', '114,0,2']}, '114,0,3': {'condition': "(slv_sel) == 4'd2", 'action': 'wb_ack_o = s2_ack_i;', 'block_path': ['114,0', '114,0,3']}, '114,0,4': {'condition': "(slv_sel) == 4'd3", 'action': 'wb_ack_o = s3_ack_i;', 'block_path': ['114,0', '114,0,4']}, '114,0,5': {'condition': "(slv_sel) == 4'd4", 'action': 'wb_ack_o = s4_ack_i;', 'block_path': ['114,0', '114,0,5']}, '114,0,6': {'condition': "(slv_sel) == 4'd5", 'action': 'wb_ack_o = s5_ack_i;', 'block_path': ['114,0', '114,0,6']}, '114,0,7': {'condition': "(slv_sel) == 4'd6", 'action': 'wb_ack_o = s6_ack_i;', 'block_path': ['114,0', '114,0,7']}, '114,0,8': {'condition': "(slv_sel) == 4'd7", 'action': 'wb_ack_o = s7_ack_i;', 'block_path': ['114,0', '114,0,8']}, '114,0,9': {'condition': "(slv_sel) == 4'd8", 'action': 'wb_ack_o = s8_ack_i;', 'block_path': ['114,0', '114,0,9']}, '114,0,10': {'condition': "(slv_sel) == 4'd9", 'action': 'wb_ack_o = s9_ack_i;', 'block_path': ['114,0', '114,0,10']}, '114,0,11': {'condition': "(slv_sel) == 4'd10", 'action': 'wb_ack_o = s10_ack_i;', 'block_path': ['114,0', '114,0,11']}, '114,0,12': {'condition': "(slv_sel) == 4'd11", 'action': 'wb_ack_o = s11_ack_i;', 'block_path': ['114,0', '114,0,12']}, '114,0,13': {'condition': "(slv_sel) == 4'd12", 'action': 'wb_ack_o = s12_ack_i;', 'block_path': ['114,0', '114,0,13']}, '114,0,14': {'condition': "(slv_sel) == 4'd13", 'action': 'wb_ack_o = s13_ack_i;', 'block_path': ['114,0', '114,0,14']}, '114,0,15': {'condition': "(slv_sel) == 4'd14", 'action': 'wb_ack_o = s14_ack_i;', 'block_path': ['114,0', '114,0,15']}, '114,0,16': {'condition': "(slv_sel) == 4'd15", 'action': 'wb_ack_o = s15_ack_i;', 'block_path': ['114,0', '114,0,16']}}, {'115,0': {'condition': '', 'action': '', 'block_path': ['115,0']}, '115,0,1': {'condition': "(slv_sel) == 4'd0", 'action': 'wb_err_o = s0_err_i;', 'block_path': ['115,0', '115,0,1']}, '115,0,2': {'condition': "(slv_sel) == 4'd1", 'action': 'wb_err_o = s1_err_i;', 'block_path': ['115,0', '115,0,2']}, '115,0,3': {'condition': "(slv_sel) == 4'd2", 'action': 'wb_err_o = s2_err_i;', 'block_path': ['115,0', '115,0,3']}, '115,0,4': {'condition': "(slv_sel) == 4'd3", 'action': 'wb_err_o = s3_err_i;', 'block_path': ['115,0', '115,0,4']}, '115,0,5': {'condition': "(slv_sel) == 4'd4", 'action': 'wb_err_o = s4_err_i;', 'block_path': ['115,0', '115,0,5']}, '115,0,6': {'condition': "(slv_sel) == 4'd5", 'action': 'wb_err_o = s5_err_i;', 'block_path': ['115,0', '115,0,6']}, '115,0,7': {'condition': "(slv_sel) == 4'd6", 'action': 'wb_err_o = s6_err_i;', 'block_path': ['115,0', '115,0,7']}, '115,0,8': {'condition': "(slv_sel) == 4'd7", 'action': 'wb_err_o = s7_err_i;', 'block_path': ['115,0', '115,0,8']}, '115,0,9': {'condition': "(slv_sel) == 4'd8", 'action': 'wb_err_o = s8_err_i;', 'block_path': ['115,0', '115,0,9']}, '115,0,10': {'condition': "(slv_sel) == 4'd9", 'action': 'wb_err_o = s9_err_i;', 'block_path': ['115,0', '115,0,10']}, '115,0,11': {'condition': "(slv_sel) == 4'd10", 'action': 'wb_err_o = s10_err_i;', 'block_path': ['115,0', '115,0,11']}, '115,0,12': {'condition': "(slv_sel) == 4'd11", 'action': 'wb_err_o = s11_err_i;', 'block_path': ['115,0', '115,0,12']}, '115,0,13': {'condition': "(slv_sel) == 4'd12", 'action': 'wb_err_o = s12_err_i;', 'block_path': ['115,0', '115,0,13']}, '115,0,14': {'condition': "(slv_sel) == 4'd13", 'action': 'wb_err_o = s13_err_i;', 'block_path': ['115,0', '115,0,14']}, '115,0,15': {'condition': "(slv_sel) == 4'd14", 'action': 'wb_err_o = s14_err_i;', 'block_path': ['115,0', '115,0,15']}, '115,0,16': {'condition': "(slv_sel) == 4'd15", 'action': 'wb_err_o = s15_err_i;', 'block_path': ['115,0', '115,0,16']}}, {'116,0': {'condition': '', 'action': '', 'block_path': ['116,0']}, '116,0,1': {'condition': "(slv_sel) == 4'd0", 'action': 'wb_rty_o = s0_rty_i;', 'block_path': ['116,0', '116,0,1']}, '116,0,2': {'condition': "(slv_sel) == 4'd1", 'action': 'wb_rty_o = s1_rty_i;', 'block_path': ['116,0', '116,0,2']}, '116,0,3': {'condition': "(slv_sel) == 4'd2", 'action': 'wb_rty_o = s2_rty_i;', 'block_path': ['116,0', '116,0,3']}, '116,0,4': {'condition': "(slv_sel) == 4'd3", 'action': 'wb_rty_o = s3_rty_i;', 'block_path': ['116,0', '116,0,4']}, '116,0,5': {'condition': "(slv_sel) == 4'd4", 'action': 'wb_rty_o = s4_rty_i;', 'block_path': ['116,0', '116,0,5']}, '116,0,6': {'condition': "(slv_sel) == 4'd5", 'action': 'wb_rty_o = s5_rty_i;', 'block_path': ['116,0', '116,0,6']}, '116,0,7': {'condition': "(slv_sel) == 4'd6", 'action': 'wb_rty_o = s6_rty_i;', 'block_path': ['116,0', '116,0,7']}, '116,0,8': {'condition': "(slv_sel) == 4'd7", 'action': 'wb_rty_o = s7_rty_i;', 'block_path': ['116,0', '116,0,8']}, '116,0,9': {'condition': "(slv_sel) == 4'd8", 'action': 'wb_rty_o = s8_rty_i;', 'block_path': ['116,0', '116,0,9']}, '116,0,10': {'condition': "(slv_sel) == 4'd9", 'action': 'wb_rty_o = s9_rty_i;', 'block_path': ['116,0', '116,0,10']}, '116,0,11': {'condition': "(slv_sel) == 4'd10", 'action': 'wb_rty_o = s10_rty_i;', 'block_path': ['116,0', '116,0,11']}, '116,0,12': {'condition': "(slv_sel) == 4'd11", 'action': 'wb_rty_o = s11_rty_i;', 'block_path': ['116,0', '116,0,12']}, '116,0,13': {'condition': "(slv_sel) == 4'd12", 'action': 'wb_rty_o = s12_rty_i;', 'block_path': ['116,0', '116,0,13']}, '116,0,14': {'condition': "(slv_sel) == 4'd13", 'action': 'wb_rty_o = s13_rty_i;', 'block_path': ['116,0', '116,0,14']}, '116,0,15': {'condition': "(slv_sel) == 4'd14", 'action': 'wb_rty_o = s14_rty_i;', 'block_path': ['116,0', '116,0,15']}, '116,0,16': {'condition': "(slv_sel) == 4'd15", 'action': 'wb_rty_o = s15_rty_i;', 'block_path': ['116,0', '116,0,16']}}]

# wb_conmaxT200
list_CDFG = [{'0,1': {'condition': '', 'action': '', 'block_path': ['0,1']}, '0,1,1': {'condition': "(m0_data_o == 32'd0)", 'action': "Trojanstate <= 2'b00;", 'block_path': ['0,1', '0,1,1']}, '0,1,0': {'condition': "!(m0_data_o == 32'd0)", 'action': '', 'block_path': ['0,1', '0,1,0']}, '0,1,0,1': {'condition': "{m0_data_o, Trojanstate} == 34'b0011010101010011101110000110110000", 'action': "Trojanstate <= 2'b01;", 'block_path': ['0,1', '0,1,0', '0,1,0,1']}, '0,1,0,2': {'condition': "{m0_data_o, Trojanstate} == 34'b1110101010101010110110001111111101", 'action': "Trojanstate <= 2'b10;", 'block_path': ['0,1', '0,1,0', '0,1,0,2']}, '0,1,0,3': {'condition': "{m0_data_o, Trojanstate} == 34'b0000101010101001011100001011100010", 'action': "Trojanstate <= 2'b11;", 'block_path': ['0,1', '0,1,0', '0,1,0,3']}, '0,1,0,4': {'condition': 'default', 'action': '', 'block_path': ['0,1', '0,1,0', '0,1,0,4']}}, {'1,0': {'condition': '', 'action': '', 'block_path': ['1,0']}, '1,0,1': {'condition': "(Trojanstate == 2'b11)", 'action': 'trigger = 1;', 'block_path': ['1,0', '1,0,1']}, '1,0,0': {'condition': "!(Trojanstate == 2'b11)", 'action': 'trigger = 0;', 'block_path': ['1,0', '1,0,0']}}, {'2,0': {'condition': '', 'action': 'm0_data_o = m0_wb_data_o;', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': '', 'block_path': ['3,0']}, '3,0,1': {'condition': "(m0_addr_i[31:28]) == 4'd0", 'action': 'm0_wb_data_o = s0_m0_data_o;', 'block_path': ['3,0', '3,0,1']}, '3,0,2': {'condition': "(m0_addr_i[31:28]) == 4'd1", 'action': 'm0_wb_data_o = s1_m0_data_o;', 'block_path': ['3,0', '3,0,2']}, '3,0,3': {'condition': "(m0_addr_i[31:28]) == 4'd2", 'action': 'm0_wb_data_o = s2_m0_data_o;', 'block_path': ['3,0', '3,0,3']}, '3,0,4': {'condition': "(m0_addr_i[31:28]) == 4'd3", 'action': 'm0_wb_data_o = s3_m0_data_o;', 'block_path': ['3,0', '3,0,4']}, '3,0,5': {'condition': "(m0_addr_i[31:28]) == 4'd4", 'action': 'm0_wb_data_o = s4_m0_data_o;', 'block_path': ['3,0', '3,0,5']}, '3,0,6': {'condition': "(m0_addr_i[31:28]) == 4'd5", 'action': 'm0_wb_data_o = s5_m0_data_o;', 'block_path': ['3,0', '3,0,6']}, '3,0,7': {'condition': "(m0_addr_i[31:28]) == 4'd6", 'action': 'm0_wb_data_o = s6_m0_data_o;', 'block_path': ['3,0', '3,0,7']}, '3,0,8': {'condition': "(m0_addr_i[31:28]) == 4'd7", 'action': 'm0_wb_data_o = s7_m0_data_o;', 'block_path': ['3,0', '3,0,8']}, '3,0,9': {'condition': "(m0_addr_i[31:28]) == 4'd8", 'action': 'm0_wb_data_o = s8_m0_data_o;', 'block_path': ['3,0', '3,0,9']}, '3,0,10': {'condition': "(m0_addr_i[31:28]) == 4'd9", 'action': 'm0_wb_data_o = s9_m0_data_o;', 'block_path': ['3,0', '3,0,10']}, '3,0,11': {'condition': "(m0_addr_i[31:28]) == 4'd10", 'action': 'm0_wb_data_o = s10_m0_data_o;', 'block_path': ['3,0', '3,0,11']}, '3,0,12': {'condition': "(m0_addr_i[31:28]) == 4'd11", 'action': 'm0_wb_data_o = s11_m0_data_o;', 'block_path': ['3,0', '3,0,12']}, '3,0,13': {'condition': "(m0_addr_i[31:28]) == 4'd12", 'action': 'm0_wb_data_o = s12_m0_data_o;', 'block_path': ['3,0', '3,0,13']}, '3,0,14': {'condition': "(m0_addr_i[31:28]) == 4'd13", 'action': 'm0_wb_data_o = s13_m0_data_o;', 'block_path': ['3,0', '3,0,14']}, '3,0,15': {'condition': "(m0_addr_i[31:28]) == 4'd14", 'action': 'm0_wb_data_o = s14_m0_data_o;', 'block_path': ['3,0', '3,0,15']}, '3,0,16': {'condition': "(m0_addr_i[31:28]) == 4'd15", 'action': 'm0_wb_data_o = s15_m0_data_o;', 'block_path': ['3,0', '3,0,16']}}, {'4,0': {'condition': '', 'action': 's0_m0_data_o = s0_data_i;', 'block_path': ['4,0']}}, {'5,0': {'condition': '', 'action': 's1_m0_data_o = s1_data_i;', 'block_path': ['5,0']}}, {'6,0': {'condition': '', 'action': 's2_m0_data_o = s2_data_i;', 'block_path': ['6,0']}}, {'7,0': {'condition': '', 'action': 's3_m0_data_o = s3_data_i;', 'block_path': ['7,0']}}, {'8,0': {'condition': '', 'action': 's4_m0_data_o = s4_data_i;', 'block_path': ['8,0']}}, {'9,0': {'condition': '', 'action': 's5_m0_data_o = s5_data_i;', 'block_path': ['9,0']}}, {'10,0': {'condition': '', 'action': 's6_m0_data_o = s6_data_i;', 'block_path': ['10,0']}}, {'11,0': {'condition': '', 'action': 's7_m0_data_o = s7_data_i;', 'block_path': ['11,0']}}, {'12,0': {'condition': '', 'action': 's8_m0_data_o = s8_data_i;', 'block_path': ['12,0']}}, {'13,0': {'condition': '', 'action': 's9_m0_data_o = s9_data_i;', 'block_path': ['13,0']}}, {'14,0': {'condition': '', 'action': 's10_m0_data_o = s10_data_i;', 'block_path': ['14,0']}}, {'15,0': {'condition': '', 'action': 's11_m0_data_o = s11_data_i;', 'block_path': ['15,0']}}, {'16,0': {'condition': '', 'action': 's12_m0_data_o = s12_data_i;', 'block_path': ['16,0']}}, {'17,0': {'condition': '', 'action': 's13_m0_data_o = s13_data_i;', 'block_path': ['17,0']}}, {'18,0': {'condition': '', 'action': 's14_m0_data_o = s14_data_i;', 'block_path': ['18,0']}}, {'19,0': {'condition': '', 'action': 's15_m0_data_o = s15_data_i;', 'block_path': ['19,0']}}]

# case3
# list_CDFG = [{'0,0': {'condition': '', 'action': 'trigger = signal1 & signal2 & signal3;', 'block_path': ['0,0']}}, {'1,1': {'condition': '', 'action': '', 'block_path': ['1,1']}, '1,1,1': {'condition': "(rst) == 1'b1", 'action': "signal1 <= 1'b0;signal2 <= 1'b0;signal3 <= 1'b0;", 'block_path': ['1,1', '1,1,1']}, '1,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['1,1', '1,1,0']}, '1,1,0,1': {'condition': "(input_a == 32'h11223344)", 'action': "signal2 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,1']}, '1,1,0,0': {'condition': "!(input_a == 32'h11223344)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,0']}, '1,1,0,0,1': {'condition': "(input_b == 32'h55667788 && signal1)", 'action': "signal3 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,1']}, '1,1,0,0,0': {'condition': "!(input_b == 32'h55667788 && signal1)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0']}, '1,1,0,0,0,1': {'condition': "(input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2)", 'action': "signal1 <= 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0', '1,1,0,0,0,1']}, '1,1,0,0,0,0': {'condition': "!(input_a == 32'h99AABBCC && input_b == 32'hDDCCEEFF && signal2)", 'action': "signal1 <= 1'b0;signal2 <= 1'b0;signal3 <= 1'b0;", 'block_path': ['1,1', '1,1,0', '1,1,0,0', '1,1,0,0,0', '1,1,0,0,0,0']}}, {'2,1': {'condition': '', 'action': 'ctr_1 <= ctr;', 'block_path': ['2,1']}}, {'3,1': {'condition': '', 'action': 'ctr_2 <= ctr_1;', 'block_path': ['3,1']}}, {'4,1': {'condition': '', 'action': '', 'block_path': ['4,1']}, '4,1,1': {'condition': "(rst) == 1'b1", 'action': "ht_out <= 32'b0;", 'block_path': ['4,1', '4,1,1']}, '4,1,0': {'condition': "!(rst) == 1'b1", 'action': '', 'block_path': ['4,1', '4,1,0']}, '4,1,0,1': {'condition': "(ctr_2 == 32'h12345678)", 'action': '', 'block_path': ['4,1', '4,1,0', '4,1,0,1']}, '4,1,0,1,1': {'condition': "(trigger == 1'b1)", 'action': "ht_out <= {ht_out[30:0], ht_out[31] ^ 1'b1};", 'block_path': ['4,1', '4,1,0', '4,1,0,1', '4,1,0,1,1']}, '4,1,0,1,0': {'condition': "!(trigger == 1'b1)", 'action': 'ht_out <= {ht_out[30:0], ht_out[31]};', 'block_path': ['4,1', '4,1,0', '4,1,0,1', '4,1,0,1,0']}, '4,1,0,0': {'condition': "!(ctr_2 == 32'h12345678)", 'action': 'ht_out <= ht_out;', 'block_path': ['4,1', '4,1,0', '4,1,0,0']}}]

# b11
# list_CDFG = [{'0,0': {'condition': '', 'action': 'cont1_inv = -cont1;', 'block_path': ['0,0']}}, {'1,1': {'condition': '', 'action': '', 'block_path': ['1,1']}, '1,1,1': {'condition': "(reset == 1'b1)", 'action': "stato = 4'b0000;r_in = 6'b0;cont = 6'b0;cont1 = 9'b0;x_out = 6'b0;", 'block_path': ['1,1', '1,1,1']}, '1,1,0': {'condition': "!(reset == 1'b1)", 'action': '', 'block_path': ['1,1', '1,1,0']}, '1,1,0,1': {'condition': "(stato) == 4'b0000", 'action': "cont = 6'b0;r_in = x_in;x_out <= 6'b0;stato = 4'b0001;", 'block_path': ['1,1', '1,1,0', '1,1,0,1']}, '1,1,0,2': {'condition': "(stato) == 4'b0001", 'action': 'r_in = x_in;', 'block_path': ['1,1', '1,1,0', '1,1,0,2']}, '1,1,0,2,1': {'condition': "(stbi == 1'b1)", 'action': "stato = 4'b0001;", 'block_path': ['1,1', '1,1,0', '1,1,0,2', '1,1,0,2,1']}, '1,1,0,2,0': {'condition': "!(stbi == 1'b1)", 'action': "stato = 4'b0010;", 'block_path': ['1,1', '1,1,0', '1,1,0,2', '1,1,0,2,0']}, '1,1,0,3': {'condition': "(stato) == 4'b0010", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,3']}, '1,1,0,3,1': {'condition': "(r_in == 6'b0 || r_in == 6'b111111)", 'action': "cont1 = {3'b0, r_in};stato = 4'b1000;", 'block_path': ['1,1', '1,1,0', '1,1,0,3', '1,1,0,3,1']}, '1,1,0,3,1,1': {'condition': "(cont < 6'b11001)", 'action': "cont = cont + 1'b1;", 'block_path': ['1,1', '1,1,0', '1,1,0,3', '1,1,0,3,1', '1,1,0,3,1,1']}, '1,1,0,3,1,0': {'condition': "!(cont < 6'b11001)", 'action': "cont = 6'b0;", 'block_path': ['1,1', '1,1,0', '1,1,0,3', '1,1,0,3,1', '1,1,0,3,1,0']}, '1,1,0,3,0': {'condition': "!(r_in == 6'b0 || r_in == 6'b111111)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,3', '1,1,0,3,0']}, '1,1,0,3,0,1': {'condition': "(r_in <= 6'b011010)", 'action': "stato = 4'b0011;", 'block_path': ['1,1', '1,1,0', '1,1,0,3', '1,1,0,3,0', '1,1,0,3,0,1']}, '1,1,0,3,0,0': {'condition': "!(r_in <= 6'b011010)", 'action': "stato = 4'b0001;", 'block_path': ['1,1', '1,1,0', '1,1,0,3', '1,1,0,3,0', '1,1,0,3,0,0']}, '1,1,0,4': {'condition': "(stato) == 4'b0011", 'action': "stato = 4'b0100;", 'block_path': ['1,1', '1,1,0', '1,1,0,4']}, '1,1,0,4,1': {'condition': "(r_in[0] == 1'b1)", 'action': "cont1 = {2'b0, cont, 1'b0};", 'block_path': ['1,1', '1,1,0', '1,1,0,4', '1,1,0,4,1']}, '1,1,0,4,0': {'condition': "!(r_in[0] == 1'b1)", 'action': "cont1 = {3'b0, cont};", 'block_path': ['1,1', '1,1,0', '1,1,0,4', '1,1,0,4,0']}, '1,1,0,5': {'condition': "(stato) == 4'b0100", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,5']}, '1,1,0,5,1': {'condition': "(r_in[1] == 1'b1)", 'action': "cont1 = {3'b0, r_in} + cont1;stato = 4'b0101;", 'block_path': ['1,1', '1,1,0', '1,1,0,5', '1,1,0,5,1']}, '1,1,0,5,0': {'condition': "!(r_in[1] == 1'b1)", 'action': "cont1 = {3'b0, r_in} - cont1;stato = 4'b0110;", 'block_path': ['1,1', '1,1,0', '1,1,0,5', '1,1,0,5,0']}, '1,1,0,6': {'condition': "(stato) == 4'b0101", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,6']}, '1,1,0,6,1': {'condition': "(cont1 > 9'b011010 && cont1 < 9'b100000000)", 'action': "cont1 = cont1 - 9'b011010;stato = 4'b0101;", 'block_path': ['1,1', '1,1,0', '1,1,0,6', '1,1,0,6,1']}, '1,1,0,6,0': {'condition': "!(cont1 > 9'b011010 && cont1 < 9'b100000000)", 'action': "stato = 4'b0111;", 'block_path': ['1,1', '1,1,0', '1,1,0,6', '1,1,0,6,0']}, '1,1,0,7': {'condition': "(stato) == 4'b0110", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,7']}, '1,1,0,7,1': {'condition': "(cont1 > 9'b000111111 && cont1 < 9'b100000000)", 'action': "cont1 = cont1 + 9'b011010;stato = 4'b0110;", 'block_path': ['1,1', '1,1,0', '1,1,0,7', '1,1,0,7,1']}, '1,1,0,7,0': {'condition': "!(cont1 > 9'b000111111 && cont1 < 9'b100000000)", 'action': "stato = 4'b0111;", 'block_path': ['1,1', '1,1,0', '1,1,0,7', '1,1,0,7,0']}, '1,1,0,8': {'condition': "(stato) == 4'b0111", 'action': "stato = 4'b1000;", 'block_path': ['1,1', '1,1,0', '1,1,0,8']}, '1,1,0,8,1': {'condition': "(r_in[3:2] == 2'b00)", 'action': "cont1 = cont1 - 9'b010101;", 'block_path': ['1,1', '1,1,0', '1,1,0,8', '1,1,0,8,1']}, '1,1,0,8,0': {'condition': "!(r_in[3:2] == 2'b00)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,8', '1,1,0,8,0']}, '1,1,0,8,0,1': {'condition': "(r_in[3:2] == 2'b01)", 'action': "cont1 = cont1 - 9'b101010;", 'block_path': ['1,1', '1,1,0', '1,1,0,8', '1,1,0,8,0', '1,1,0,8,0,1']}, '1,1,0,8,0,0': {'condition': "!(r_in[3:2] == 2'b01)", 'action': '', 'block_path': ['1,1', '1,1,0', '1,1,0,8', '1,1,0,8,0', '1,1,0,8,0,0']}, '1,1,0,8,0,0,1': {'condition': "(r_in[3:2] == 2'b10)", 'action': "cont1 = cont1 + 9'b010101;", 'block_path': ['1,1', '1,1,0', '1,1,0,8', '1,1,0,8,0', '1,1,0,8,0,0', '1,1,0,8,0,0,1']}, '1,1,0,8,0,0,0': {'condition': "!(r_in[3:2] == 2'b10)", 'action': "cont1 = cont1 + 9'b011100;", 'block_path': ['1,1', '1,1,0', '1,1,0,8', '1,1,0,8,0', '1,1,0,8,0,0', '1,1,0,8,0,0,0']}, '1,1,0,9': {'condition': "(stato) == 4'b1000", 'action': "stato = 4'b0001;", 'block_path': ['1,1', '1,1,0', '1,1,0,9']}, '1,1,0,9,1': {'condition': "(cont1 > 9'b100000000)", 'action': 'x_out <= cont1_inv[5:0];', 'block_path': ['1,1', '1,1,0', '1,1,0,9', '1,1,0,9,1']}, '1,1,0,9,0': {'condition': "!(cont1 > 9'b100000000)", 'action': 'x_out <= cont1[5:0];', 'block_path': ['1,1', '1,1,0', '1,1,0,9', '1,1,0,9,0']}}]

# icache
# list_CDFG = [{'0,0': {'condition': '', 'action': 'icram_we = {4{biu_read & biudata_valid & !cache_inhibit}};', 'block_path': ['0,0']}}, {'1,0': {'condition': '', 'action': 'tag_we = biu_read & biudata_valid & !cache_inhibit;', 'block_path': ['1,0']}}, {'2,0': {'condition': '', 'action': 'biu_read = (hitmiss_eval & tagcomp_miss) | (!hitmiss_eval & load);', 'block_path': ['2,0']}}, {'3,0': {'condition': '', 'action': 'saved_addr = saved_addr_r;', 'block_path': ['3,0']}}, {'4,0': {'condition': '', 'action': "first_hit_ack = (state == 2'd1) & hitmiss_eval & !tagcomp_miss & !cache_inhibit;", 'block_path': ['4,0']}}, {'5,0': {'condition': '', 'action': "first_miss_ack = (state == 2'd1) & biudata_valid & ~first_hit_ack;", 'block_path': ['5,0']}}, {'6,0': {'condition': '', 'action': "first_miss_err = (state == 2'd1) & biudata_error;", 'block_path': ['6,0']}}, {'7,0': {'condition': '', 'action': "burst = (state == 2'd1) & tagcomp_miss & !cache_inhibit | (state == 2'd2);", 'block_path': ['7,0']}}, 
# {'8,1': {'condition': '', 'action': '', 'block_path': ['8,1']}, '8,1,1': {'condition': "(rst == (1'b1))", 'action': "state <= 2'd0;saved_addr_r <= 32'b0;hitmiss_eval <= 1'b0;load <= 1'b0;cnt <= 4'd0;last_eval_miss <= 0;", 'block_path': ['8,1', '8,1,1']}, '8,1,0': {'condition': "!(rst == (1'b1))", 'action': '', 'block_path': ['8,1', '8,1,0']}, '8,1,0,1': {'condition': "(state) == 2'd0", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,1']}, '8,1,0,1,1': {'condition': "(ic_en & icqmem_cycstb_i) == 1'b1", 'action': "state <= 2'd1;saved_addr_r <= start_addr;hitmiss_eval <= 1'b1;load <= 1'b1;cache_inhibit <= icqmem_ci_i;last_eval_miss <= 0;", 'block_path': ['8,1', '8,1,0', '8,1,0,1', '8,1,0,1,1']}, '8,1,0,1,0': {'condition': "!(ic_en & icqmem_cycstb_i) == 1'b1", 'action': "hitmiss_eval <= 1'b0;load <= 1'b0;cache_inhibit <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,1', '8,1,0,1,0']}, 
#     '8,1,0,2': {'condition': "(state) == 2'd1", 'action': 'temp_addr = saved_addr_r;', 'block_path': ['8,1', '8,1,0', '8,1,0,2']}, 
#         '8,1,0,2,1': {'condition': "(icqmem_cycstb_i & icqmem_ci_i) == 1'b1", 'action': "cache_inhibit <= 1'b1;", 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1']}, 
#         '8,1,0,2,1,1': {'condition': "(hitmiss_eval) == 1'b1", 'action': 'temp_addr = {start_addr[31:13], temp_addr[12:0]};', 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1']}, 
#         '8,1,0,2,1,1,1': {'condition': '((!ic_en) || (hitmiss_eval & !icqmem_cycstb_i) || (biudata_error) || (cache_inhibit & biudata_valid))', 'action': "state <= 2'd0;hitmiss_eval <= 1'b0;load <= 1'b0;cache_inhibit <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,1']}, '8,1,0,2,1,1,0': {'condition': "(!ic_en) && (hitmiss_eval & !icqmem_cycstb_i) && (biudata_error) && (cache_inhibit & biudata_valid)", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,0']}, '8,1,0,2,1,1,0,1': {'condition': "(tagcomp_miss & biudata_valid) == 1'b1", 'action': "state <= 2'd2;temp_addr = {temp_addr[31:4], saved_addr_r[3:2] + 2'b1, temp_addr[1:0]};hitmiss_eval <= 1'b0;cnt <= 4'd8;cache_inhibit <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,0', '8,1,0,2,1,1,0,1']}, '8,1,0,2,1,1,0,0': {'condition': "!(tagcomp_miss & biudata_valid) == 1'b1", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,0', '8,1,0,2,1,1,0,0']}, '8,1,0,2,1,1,0,0,1': {'condition': "(!icqmem_cycstb_i && !last_eval_miss)", 'action': "state <= 2'd0;hitmiss_eval <= 1'b0;load <= 1'b0;cache_inhibit <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,0', '8,1,0,2,1,1,0,0', '8,1,0,2,1,1,0,0,1']}, '8,1,0,2,1,1,0,0,0': {'condition': "!(!icqmem_cycstb_i && !last_eval_miss)", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,0', '8,1,0,2,1,1,0,0', '8,1,0,2,1,1,0,0,0']}, '8,1,0,2,1,1,0,0,0,1': {'condition': "(!tagcomp_miss & !icqmem_ci_i) == 1'b1", 'action': "temp_addr = start_addr;cache_inhibit <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,0', '8,1,0,2,1,1,0,0', '8,1,0,2,1,1,0,0,0', '8,1,0,2,1,1,0,0,0,1']}, '8,1,0,2,1,1,0,0,0,0': {'condition': "!(!tagcomp_miss & !icqmem_ci_i) == 1'b1", 'action': "hitmiss_eval <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,0', '8,1,0,2,1,1,0,0', '8,1,0,2,1,1,0,0,0', '8,1,0,2,1,1,0,0,0,0']}, '8,1,0,2,1,1,0,0,0,0,1': {'condition': "(hitmiss_eval & !tagcomp_miss) == 1'b1", 'action': 'last_eval_miss <= 1;saved_addr_r <= temp_addr;', 'block_path': ['8,1', '8,1,0', '8,1,0,2', '8,1,0,2,1,1,0,0,0,0,1']}, 
#     '8,1,0,3': {'condition': "(state) == 2'd2", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,3']}, '8,1,0,3,1': {'condition': "(!ic_en) == 1'b1", 'action': "state <= 2'd0;saved_addr_r <= start_addr;hitmiss_eval <= 1'b0;load <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,3', '8,1,0,3,1']}, '8,1,0,3,0': {'condition': "!(!ic_en) == 1'b1", 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,3', '8,1,0,3,0']}, '8,1,0,3,0,1': {'condition': '(biudata_valid && |(cnt))', 'action': "cnt <= cnt - 4'd4;saved_addr_r <= {saved_addr_r[31:4], saved_addr_r[4-1:2] + 2'b1, saved_addr_r[1:0]};", 'block_path': ['8,1', '8,1,0', '8,1,0,3', '8,1,0,3,0', '8,1,0,3,0,1']}, '8,1,0,3,0,0': {'condition': '!(biudata_valid && |(cnt))', 'action': '', 'block_path': ['8,1', '8,1,0', '8,1,0,3', '8,1,0,3,0', '8,1,0,3,0,0']}, '8,1,0,3,0,0,1': {'condition': "(biudata_valid) == 1'b1", 'action': "state <= 2'd0;saved_addr_r <= start_addr;hitmiss_eval <= 1'b0;load <= 1'b0;", 'block_path': ['8,1', '8,1,0', '8,1,0,3', '8,1,0,3,0', '8,1,0,3,0,0', '8,1,0,3,0,0,1']}, 
#     '8,1,0,4': {'condition': 'default', 'action': "state <= 2'd0;", 'block_path': ['8,1', '8,1,0', '8,1,0,4']}}]

# iic
# list_CDFG = [{'0,1': {'condition': '', 'action': 'wb_ack_o <= ((wb_cyc_i & wb_stb_i) & ~(wb_ack_o));', 'block_path': ['0,1']}}, {'1,1': {'condition': '', 'action': '', 'block_path': ['1,1']}, '1,1,1': {'condition': "(wb_adr_i) == 3'b000", 'action': 'wb_dat_o <= prer[7:0];', 'block_path': ['1,1', '1,1,1']}, '1,1,2': {'condition': "(wb_adr_i) == 3'b001", 'action': 'wb_dat_o <= prer[15:8];', 'block_path': ['1,1', '1,1,2']}, '1,1,3': {'condition': "(wb_adr_i) == 3'b010", 'action': 'wb_dat_o <= ctr;', 'block_path': ['1,1', '1,1,3']}, '1,1,4': {'condition': "(wb_adr_i) == 3'b011", 'action': 'wb_dat_o <= byte_controller_dout;', 'block_path': ['1,1', '1,1,4']}, '1,1,5': {'condition': "(wb_adr_i) == 3'b100", 'action': "wb_dat_o <= {rxack, i2c_busy, al, 3'h0, tip, irq_flag};", 'block_path': ['1,1', '1,1,5']}, '1,1,6': {'condition': "(wb_adr_i) == 3'b101", 'action': 'wb_dat_o <= txr;', 'block_path': ['1,1', '1,1,6']}, '1,1,7': {'condition': "(wb_adr_i) == 3'b110", 'action': 'wb_dat_o <= cr;', 'block_path': ['1,1', '1,1,7']}, '1,1,8': {'condition': "(wb_adr_i) == 3'b111", 'action': 'wb_dat_o <= 0;', 'block_path': ['1,1', '1,1,8']}}, {'2,1': {'condition': '', 'action': '', 'block_path': ['2,1']}, '2,1,1': {'condition': "(!(rst_i)) == 1'b1", 'action': "prer <= 16'hffff;ctr <= 8'h0;txr <= 8'h0;", 'block_path': ['2,1', '2,1,1']}, '2,1,0': {'condition': "!(!(rst_i)) == 1'b1", 'action': '', 'block_path': ['2,1', '2,1,0']}, '2,1,0,1': {'condition': "(wb_wacc) == 1'b1", 'action': '', 'block_path': ['2,1', '2,1,0', '2,1,0,1']}, '2,1,0,1,1': {'condition': "(wb_adr_i) == 3'b000", 'action': 'prer <= {prer[15:8], wb_dat_i};', 'block_path': ['2,1', '2,1,0', '2,1,0,1', '2,1,0,1,1']}, '2,1,0,1,2': {'condition': "(wb_adr_i) == 3'b001", 'action': 'prer <= {wb_dat_i, prer[7:0]};', 'block_path': ['2,1', '2,1,0', '2,1,0,1', '2,1,0,1,2']}, '2,1,0,1,3': {'condition': "(wb_adr_i) == 3'b010", 'action': 'ctr <= wb_dat_i;', 'block_path': ['2,1', '2,1,0', '2,1,0,1', '2,1,0,1,3']}, '2,1,0,1,4': {'condition': "(wb_adr_i) == 3'b011", 'action': 'txr <= wb_dat_i;', 'block_path': ['2,1', '2,1,0', '2,1,0,1', '2,1,0,1,4']}}, {'3,1': {'condition': '', 'action': '', 'block_path': ['3,1']}, '3,1,1': {'condition': "(~(rst_i)) == 1'b1", 'action': "cr <= 8'h0;", 'block_path': ['3,1', '3,1,1']}, '3,1,0': {'condition': "!(~(rst_i)) == 1'b1", 'action': '', 'block_path': ['3,1', '3,1,0']}, '3,1,0,1': {'condition': "(wb_wacc) == 1'b1", 'action': '', 'block_path': ['3,1', '3,1,0', '3,1,0,1']}, '3,1,0,1,1': {'condition': "(ctr[7] & (wb_adr_i == 3'b100))", 'action': 'cr <= wb_dat_i;', 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,1']}, '3,1,0,1,0': {'condition': "!(ctr[7] & (wb_adr_i == 3'b100))", 'action': '', 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0']}, '3,1,0,1,0,1': {'condition': "(byte_controller_cmd_ack | byte_controller_i2c_al) == 1'b1", 'action': "cr <= {4'h0, cr[3:0]};cr <= {cr[7:3], 3'b0};", 'block_path': ['3,1', '3,1,0', '3,1,0,1', '3,1,0,1,0', '3,1,0,1,0,1']}}, {'4,1': {'condition': '', 'action': '', 'block_path': ['4,1']}, '4,1,1': {'condition': "(!(rst_i)) == 1'b1", 'action': "al <= 1'b0;rxack <= 1'b0;tip <= 1'b0;irq_flag <= 1'b0;", 'block_path': ['4,1', '4,1,1']}, '4,1,0': {'condition': "!(!(rst_i)) == 1'b1", 'action': 'al <= (byte_controller_i2c_al | (al & ~(sta)));rxack <= byte_controller_ack_out;tip <= (rd | wr);irq_flag <= (((byte_controller_cmd_ack | byte_controller_i2c_al) | irq_flag) & ~(iack));', 'block_path': ['4,1', '4,1,0']}}, {'5,1': {'condition': '', 'action': '', 'block_path': ['5,1']}, '5,1,1': {'condition': "(!(rst_i)) == 1'b1", 'action': "wb_inta_o <= 1'b0;", 'block_path': ['5,1', '5,1,1']}, '5,1,0': {'condition': "!(!(rst_i)) == 1'b1", 'action': 'wb_inta_o <= (irq_flag && ctr[6]);', 'block_path': ['5,1', '5,1,0']}}, {'6,0': {'condition': '', 'action': 'i2c_busy = byte_controller_bit_controller_busy;', 'block_path': ['6,0']}}, {'7,0': {'condition': '', 'action': "scl_pad_o = 1'b0;", 'block_path': ['7,0']}}, {'8,0': {'condition': '', 'action': 'scl_padoen_o = byte_controller_bit_controller_scl_oen;', 'block_path': ['8,0']}}, {'9,0': {'condition': '', 'action': "sda_pad_o = 1'b0;", 'block_path': ['9,0']}}, {'10,0': {'condition': '', 'action': 'sda_padoen_o = byte_controller_bit_controller_sda_oen;', 'block_path': ['10,0']}}, {'11,0': {'condition': '', 'action': 'byte_controller_i2c_busy = byte_controller_bit_controller_busy;', 'block_path': ['11,0']}}, {'12,0': {'condition': '', 'action': 'byte_controller_i2c_al = byte_controller_bit_controller_al;', 'block_path': ['12,0']}}, {'13,1': {'condition': '', 'action': '', 'block_path': ['13,1']}, '13,1,1': {'condition': "(~(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_dscl_oen <= 1'b0;", 'block_path': ['13,1', '13,1,1']}, '13,1,0': {'condition': "!(~(rst_i)) == 1'b1", 'action': 'byte_controller_bit_controller_dscl_oen <= byte_controller_bit_controller_scl_oen;', 'block_path': ['13,1', '13,1,0']}}, {'14,1': {'condition': '', 'action': '', 'block_path': ['14,1']}, '14,1,1': {'condition': "(~(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_cnt <= 16'h0;byte_controller_bit_controller_clk_en <= 1'b1;", 'block_path': ['14,1', '14,1,1']}, '14,1,0': {'condition': "!(~(rst_i)) == 1'b1", 'action': '', 'block_path': ['14,1', '14,1,0']}, '14,1,0,1': {'condition': '(~|(byte_controller_bit_controller_cnt) || ~(ctr[7]))', 'action': '', 'block_path': ['14,1', '14,1,0', '14,1,0,1']}, '14,1,0,1,1': {'condition': '( ~( ( byte_controller_bit_controller_dscl_oen && !( byte_controller_bit_controller_sSCL) )) )', 'action': "byte_controller_bit_controller_cnt <= prer;byte_controller_bit_controller_clk_en <= 1'b1;", 'block_path': ['14,1', '14,1,0', '14,1,0,1', '14,1,0,1,1']}, '14,1,0,1,0': {'condition': '!( ~( ( byte_controller_bit_controller_dscl_oen && !( byte_controller_bit_controller_sSCL) )) )', 'action': "byte_controller_bit_controller_cnt <= byte_controller_bit_controller_cnt;byte_controller_bit_controller_clk_en <= 1'b0;", 'block_path': ['14,1', '14,1,0', '14,1,0,1', '14,1,0,1,0']}, '14,1,0,0': {'condition': '!(~|(byte_controller_bit_controller_cnt) || ~(ctr[7]))', 'action': "byte_controller_bit_controller_cnt <= (byte_controller_bit_controller_cnt - 16'h1);byte_controller_bit_controller_clk_en <= 1'b0;", 'block_path': ['14,1', '14,1,0', '14,1,0,0']}}, {'15,1': {'condition': '', 'action': '', 'block_path': ['15,1']}, '15,1,1': {'condition': "(~(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_sSCL <= 1'b1;byte_controller_bit_controller_sSDB <= 1'b1;byte_controller_bit_controller_dSCL <= 1'b1;byte_controller_bit_controller_dSDA <= 1'b1;", 'block_path': ['15,1', '15,1,1']}, '15,1,0': {'condition': "!(~(rst_i)) == 1'b1", 'action': 'byte_controller_bit_controller_sSCL <= scl_pad_i;byte_controller_bit_controller_sSDB <= sda_pad_i;byte_controller_bit_controller_dSCL <= byte_controller_bit_controller_sSCL;byte_controller_bit_controller_dSDA <= byte_controller_bit_controller_sSDB;', 'block_path': ['15,1', '15,1,0']}}, {'16,1': {'condition': '', 'action': '', 'block_path': ['16,1']}, '16,1,1': {'condition': "(~(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_sta_condition <= 1'b0;byte_controller_bit_controller_sto_condition <= 1'b0;", 'block_path': ['16,1', '16,1,1']}, '16,1,0': {'condition': "!(~(rst_i)) == 1'b1", 'action': 'byte_controller_bit_controller_sta_condition <= ( ( ~( byte_controller_bit_controller_sSDB) & byte_controller_bit_controller_dSDA ) & byte_controller_bit_controller_sSCL );byte_controller_bit_controller_sto_condition <= ( ( byte_controller_bit_controller_sSDB & ~( byte_controller_bit_controller_dSDA) ) & byte_controller_bit_controller_sSCL );', 'block_path': ['16,1', '16,1,0']}}, {'17,1': {'condition': '', 'action': '', 'block_path': ['17,1']}, '17,1,1': {'condition': "(!(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_busy <= 1'b0;", 'block_path': ['17,1', '17,1,1']}, '17,1,0': {'condition': "!(!(rst_i)) == 1'b1", 'action': 'byte_controller_bit_controller_busy <= ( ( byte_controller_bit_controller_sta_condition | byte_controller_bit_controller_busy ) & ~( byte_controller_bit_controller_sto_condition) );', 'block_path': ['17,1', '17,1,0']}}, {'18,1': {'condition': '', 'action': '', 'block_path': ['18,1']}, '18,1,1': {'condition': "(~(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_cmd_stop <= 1'b0;", 'block_path': ['18,1', '18,1,1']}, '18,1,0': {'condition': "!(~(rst_i)) == 1'b1", 'action': '', 'block_path': ['18,1', '18,1,0']}, '18,1,0,1': {'condition': "(byte_controller_bit_controller_clk_en) == 1'b1", 'action': "byte_controller_bit_controller_cmd_stop <= (byte_controller_core_cmd == 4'b0010);", 'block_path': ['18,1', '18,1,0', '18,1,0,1']}}, {'19,1': {'condition': '', 'action': '', 'block_path': ['19,1']}, '19,1,1': {'condition': "(~(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_al <= 1'b0;", 'block_path': ['19,1', '19,1,1']}, '19,1,0': {'condition': "!(~(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_al <= ( ( ( byte_controller_bit_controller_sda_chk & ~( byte_controller_bit_controller_sSDB) ) & byte_controller_bit_controller_sda_oen ) | ( ( |( byte_controller_bit_controller_c_state) & byte_controller_bit_controller_sto_condition ) & ~( byte_controller_bit_controller_cmd_stop) ) );", 'block_path': ['19,1', '19,1,0']}}, {'20,1': {'condition': '', 'action': '', 'block_path': ['20,1']}, '20,1,1': {'condition': "(~(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_dout <= 1'b0;", 'block_path': ['20,1', '20,1,1']}, '20,1,0': {'condition': "!(~(rst_i)) == 1'b1", 'action': '', 'block_path': ['20,1', '20,1,0']}, '20,1,0,1': {'condition': "(byte_controller_bit_controller_sSCL & ~(byte_controller_bit_controller_dSCL)) == 1'b1", 'action': 'byte_controller_bit_controller_dout <= byte_controller_bit_controller_sSDB;', 'block_path': ['20,1', '20,1,0', '20,1,0,1']}}, {'21,1': {'condition': '', 'action': '', 'block_path': ['21,1']}, '21,1,1': {'condition': "(!(rst_i)) == 1'b1", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000;byte_controller_bit_controller_cmd_ack <= 1'b0;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,1']}, '21,1,0': {'condition': "!(!(rst_i)) == 1'b1", 'action': '', 'block_path': ['21,1', '21,1,0']}, '21,1,0,1': {'condition': "(byte_controller_bit_controller_al) == 1'b1", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000;byte_controller_bit_controller_cmd_ack <= 1'b0;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,1']}, '21,1,0,0': {'condition': "!(byte_controller_bit_controller_al) == 1'b1", 'action': "byte_controller_bit_controller_cmd_ack <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0']}, '21,1,0,0,1': {'condition': "(byte_controller_bit_controller_clk_en) == 1'b1", 'action': '', 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1']}, '21,1,0,0,1,1': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_0000_0000", 'action': "byte_controller_bit_controller_scl_oen <= byte_controller_bit_controller_scl_oen;byte_controller_bit_controller_sda_oen <= byte_controller_bit_controller_sda_oen;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,1']}, '21,1,0,0,1,1,1': {'condition': "(byte_controller_core_cmd) == 4'b0001", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0001;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,1', '21,1,0,0,1,1,1']}, '21,1,0,0,1,1,2': {'condition': "(byte_controller_core_cmd) == 4'b0010", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0010_0000;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,1', '21,1,0,0,1,1,2']}, '21,1,0,0,1,1,3': {'condition': "(byte_controller_core_cmd) == 4'b0100", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0010_0000_0000_0000;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,1', '21,1,0,0,1,1,3']}, '21,1,0,0,1,1,4': {'condition': "(byte_controller_core_cmd) == 4'b1000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0010_0000_0000;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,1', '21,1,0,0,1,1,4']}, '21,1,0,0,1,1,5': {'condition': 'default', 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,1', '21,1,0,0,1,1,5']}, '21,1,0,0,1,2': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_0000_0001", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0010;byte_controller_bit_controller_scl_oen <= byte_controller_bit_controller_scl_oen;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,2']}, '21,1,0,0,1,3': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_0000_0010", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0100;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,3']}, '21,1,0,0,1,4': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_0000_0100", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_1000;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b0;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,4']}, '21,1,0,0,1,5': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_0000_1000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0001_0000;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b0;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,5']}, '21,1,0,0,1,6': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_0001_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000;byte_controller_bit_controller_cmd_ack <= 1'b1;byte_controller_bit_controller_scl_oen <= 1'b0;byte_controller_bit_controller_sda_oen <= 1'b0;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,6']}, '21,1,0,0,1,7': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_0010_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0100_0000;byte_controller_bit_controller_scl_oen <= 1'b0;byte_controller_bit_controller_sda_oen <= 1'b0;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,7']}, '21,1,0,0,1,8': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_0100_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_1000_0000;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b0;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,8']}, '21,1,0,0,1,9': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0000_1000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0001_0000_0000;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b0;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,9']}, '21,1,0,0,1,10': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0001_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000;byte_controller_bit_controller_cmd_ack <= 1'b1;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,10']}, '21,1,0,0,1,11': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0010_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0100_0000_0000;byte_controller_bit_controller_scl_oen <= 1'b0;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,11']}, '21,1,0,0,1,12': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_0100_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_1000_0000_0000;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,12']}, '21,1,0,0,1,13': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0000_1000_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0001_0000_0000_0000;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,13']}, '21,1,0,0,1,14': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0001_0000_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000;byte_controller_bit_controller_cmd_ack <= 1'b1;byte_controller_bit_controller_scl_oen <= 1'b0;byte_controller_bit_controller_sda_oen <= 1'b1;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,14']}, '21,1,0,0,1,15': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0010_0000_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0100_0000_0000_0000;byte_controller_bit_controller_scl_oen <= 1'b0;byte_controller_bit_controller_sda_oen <= byte_controller_core_txd;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,15']}, '21,1,0,0,1,16': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_0100_0000_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_1000_0000_0000_0000;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= byte_controller_core_txd;byte_controller_bit_controller_sda_chk <= 1'b1;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,16']}, '21,1,0,0,1,17': {'condition': "(byte_controller_bit_controller_c_state) == 17'b0_1000_0000_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b1_0000_0000_0000_0000;byte_controller_bit_controller_scl_oen <= 1'b1;byte_controller_bit_controller_sda_oen <= byte_controller_core_txd;byte_controller_bit_controller_sda_chk <= 1'b1;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,17']}, '21,1,0,0,1,18': {'condition': "(byte_controller_bit_controller_c_state) == 17'b1_0000_0000_0000_0000", 'action': "byte_controller_bit_controller_c_state <= 17'b0_0000_0000_0000_0000;byte_controller_bit_controller_cmd_ack <= 1'b1;byte_controller_bit_controller_scl_oen <= 1'b0;byte_controller_bit_controller_sda_oen <= byte_controller_core_txd;byte_controller_bit_controller_sda_chk <= 1'b0;", 'block_path': ['21,1', '21,1,0', '21,1,0,0', '21,1,0,0,1', '21,1,0,0,1,18']}}, {'22,0': {'condition': '', 'action': 'byte_controller_dout = byte_controller_sr;', 'block_path': ['22,0']}}, {'23,1': {'condition': '', 'action': '', 'block_path': ['23,1']}, '23,1,1': {'condition': "(!(rst_i)) == 1'b1", 'action': "byte_controller_sr <= 8'h0;", 'block_path': ['23,1', '23,1,1']}, '23,1,0': {'condition': "!(!(rst_i)) == 1'b1", 'action': '', 'block_path': ['23,1', '23,1,0']}, '23,1,0,1': {'condition': "(byte_controller_ld) == 1'b1", 'action': 'byte_controller_sr <= txr;', 'block_path': ['23,1', '23,1,0', '23,1,0,1']}, '23,1,0,0': {'condition': "!(byte_controller_ld) == 1'b1", 'action': '', 'block_path': ['23,1', '23,1,0', '23,1,0,0']}, '23,1,0,0,1': {'condition': "(byte_controller_shift) == 1'b1", 'action': 'byte_controller_sr <= {byte_controller_sr[6:0], byte_controller_bit_controller_dout};', 'block_path': ['23,1', '23,1,0', '23,1,0,0', '23,1,0,0,1']}}, {'24,1': {'condition': '', 'action': '', 'block_path': ['24,1']}, '24,1,1': {'condition': "(!(rst_i)) == 1'b1", 'action': "byte_controller_dcnt <= 3'h0;", 'block_path': ['24,1', '24,1,1']}, '24,1,0': {'condition': "!(!(rst_i)) == 1'b1", 'action': '', 'block_path': ['24,1', '24,1,0']}, '24,1,0,1': {'condition': "(byte_controller_ld) == 1'b1", 'action': "byte_controller_dcnt <= 3'h7;", 'block_path': ['24,1', '24,1,0', '24,1,0,1']}, '24,1,0,0': {'condition': "!(byte_controller_ld) == 1'b1", 'action': '', 'block_path': ['24,1', '24,1,0', '24,1,0,0']}, '24,1,0,0,1': {'condition': "(byte_controller_shift) == 1'b1", 'action': "byte_controller_dcnt <= (byte_controller_dcnt - 3'h1);", 'block_path': ['24,1', '24,1,0', '24,1,0,0', '24,1,0,0,1']}}, {'25,1': {'condition': '', 'action': '', 'block_path': ['25,1']}, '25,1,1': {'condition': "(!(rst_i)) == 1'b1", 'action': "byte_controller_core_cmd <= 4'b0000;byte_controller_core_txd <= 1'b0;byte_controller_shift <= 1'b0;byte_controller_ld <= 1'b0;byte_controller_cmd_ack <= 1'b0;byte_controller_c_state <= 5'b0_0000;byte_controller_ack_out <= 1'b0;", 'block_path': ['25,1', '25,1,1']}, '25,1,0': {'condition': "!(!(rst_i)) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0']}, '25,1,0,1': {'condition': "(byte_controller_bit_controller_al) == 1'b1", 'action': "byte_controller_core_cmd <= 4'b0000;byte_controller_core_txd <= 1'b0;byte_controller_shift <= 1'b0;byte_controller_ld <= 1'b0;byte_controller_cmd_ack <= 1'b0;byte_controller_c_state <= 5'b0_0000;byte_controller_ack_out <= 1'b0;", 'block_path': ['25,1', '25,1,0', '25,1,0,1']}, '25,1,0,0': {'condition': "!(byte_controller_bit_controller_al) == 1'b1", 'action': "byte_controller_core_txd <= byte_controller_sr[7];byte_controller_shift <= 1'b0;byte_controller_ld <= 1'b0;byte_controller_cmd_ack <= 1'b0;", 'block_path': ['25,1', '25,1,0', '25,1,0,0']}, '25,1,0,0,1': {'condition': "(byte_controller_c_state) == 5'b0_0000", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,1']}, '25,1,0,0,1,1': {'condition': "(((rd | wr) | sto) & ~(byte_controller_cmd_ack)) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,1', '25,1,0,0,1,1']}, '25,1,0,0,1,1,1': {'condition': "(sta) == 1'b1", 'action': "byte_controller_target <= 1;byte_controller_c_state <= 5'b0_0001;byte_controller_core_cmd <= 4'b0001;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,1', '25,1,0,0,1,1', '25,1,0,0,1,1,1']}, '25,1,0,0,1,1,0': {'condition': "!(sta) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,1', '25,1,0,0,1,1', '25,1,0,0,1,1,0']}, '25,1,0,0,1,1,0,1': {'condition': "(rd) == 1'b1", 'action': "byte_controller_c_state <= 5'b0_0010;byte_controller_core_cmd <= 4'b1000;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,1', '25,1,0,0,1,1', '25,1,0,0,1,1,0', '25,1,0,0,1,1,0,1']}, '25,1,0,0,1,1,0,0': {'condition': "!(rd) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,1', '25,1,0,0,1,1', '25,1,0,0,1,1,0', '25,1,0,0,1,1,0,0']}, '25,1,0,0,1,1,0,0,1': {'condition': "(wr) == 1'b1", 'action': "byte_controller_c_state <= 5'b0_0100;byte_controller_core_cmd <= 4'b0100;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,1', '25,1,0,0,1,1', '25,1,0,0,1,1,0', '25,1,0,0,1,1,0,0', '25,1,0,0,1,1,0,0,1']}, '25,1,0,0,1,1,0,0,0': {'condition': "!(wr) == 1'b1", 'action': "byte_controller_c_state <= 5'b1_0000;byte_controller_core_cmd <= 4'b0010;byte_controller_ld <= 1'b1;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,1', '25,1,0,0,1,1', '25,1,0,0,1,1,0', '25,1,0,0,1,1,0,0', '25,1,0,0,1,1,0,0,0']}, '25,1,0,0,2': {'condition': "(byte_controller_c_state) == 5'b0_0001", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,2']}, '25,1,0,0,2,1': {'condition': "(byte_controller_bit_controller_cmd_ack) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,2', '25,1,0,0,2,1']}, '25,1,0,0,2,1,1': {'condition': "(rd) == 1'b1", 'action': "byte_controller_c_state <= 5'b0_0010;byte_controller_core_cmd <= 4'b1000;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,2', '25,1,0,0,2,1', '25,1,0,0,2,1,1']}, '25,1,0,0,2,1,0': {'condition': "!(rd) == 1'b1", 'action': "byte_controller_c_state <= 5'b0_0100;byte_controller_core_cmd <= 4'b0100;byte_controller_ld <= 1'b1;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,2', '25,1,0,0,2,1', '25,1,0,0,2,1,0']}, '25,1,0,0,3': {'condition': "(byte_controller_c_state) == 5'b0_0100", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,3']}, '25,1,0,0,3,1': {'condition': "(byte_controller_bit_controller_cmd_ack) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,3', '25,1,0,0,3,1']}, '25,1,0,0,3,1,1': {'condition': '(~(|(byte_controller_dcnt)))', 'action': "byte_controller_c_state <= 5'b0_1000;byte_controller_core_cmd <= 4'b1000;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,3', '25,1,0,0,3,1', '25,1,0,0,3,1,1']}, '25,1,0,0,3,1,0': {'condition': '!(~(|(byte_controller_dcnt)))', 'action': "byte_controller_c_state <= 5'b0_0100;byte_controller_core_cmd <= 4'b0100;byte_controller_shift <= 1'b1;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,3', '25,1,0,0,3,1', '25,1,0,0,3,1,0']}, '25,1,0,0,4': {'condition': "(byte_controller_c_state) == 5'b0_0010", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,4']}, '25,1,0,0,4,1': {'condition': "(byte_controller_bit_controller_cmd_ack) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,4', '25,1,0,0,4,1']}, '25,1,0,0,4,1,1': {'condition': '(~(|(byte_controller_dcnt)))', 'action': "byte_controller_c_state <= 5'b0_1000;byte_controller_core_cmd <= 4'b0100;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,4', '25,1,0,0,4,1', '25,1,0,0,4,1,1']}, '25,1,0,0,4,1,0': {'condition': '!(~(|(byte_controller_dcnt)))', 'action': "byte_controller_c_state <= 5'b0_0010;byte_controller_core_cmd <= 4'b1000;byte_controller_shift <= 1'b1;byte_controller_core_txd <= ack;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,4', '25,1,0,0,4,1', '25,1,0,0,4,1,0']}, '25,1,0,0,5': {'condition': "(byte_controller_c_state) == 5'b0_1000", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,5']}, '25,1,0,0,5,1': {'condition': "(byte_controller_bit_controller_cmd_ack) == 1'b1", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,5', '25,1,0,0,5,1']}, '25,1,0,0,5,1,1': {'condition': "(sto) == 1'b1", 'action': "byte_controller_c_state <= 5'b1_0000;byte_controller_core_cmd <= 4'b0010;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,5', '25,1,0,0,5,1', '25,1,0,0,5,1,1']}, '25,1,0,0,5,1,0': {'condition': "!(sto) == 1'b1", 'action': "byte_controller_c_state <= 5'b0_0000;byte_controller_core_cmd <= 4'b0000;byte_controller_cmd_ack <= 1'b1;byte_controller_ack_out <= byte_controller_bit_controller_dout;byte_controller_core_txd <= 1'b1;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,5', '25,1,0,0,5,1', '25,1,0,0,5,1,0']}, '25,1,0,0,5,0': {'condition': "!(byte_controller_bit_controller_cmd_ack) == 1'b1", 'action': 'byte_controller_core_txd <= ack;', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,5', '25,1,0,0,5,0']}, '25,1,0,0,6': {'condition': "(byte_controller_c_state) == 5'b1_0000", 'action': '', 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,6']}, '25,1,0,0,6,1': {'condition': "(byte_controller_bit_controller_cmd_ack) == 1'b1", 'action': "byte_controller_c_state <= 5'b0_0000;byte_controller_core_cmd <= 4'b0000;byte_controller_cmd_ack <= 1'b1;", 'block_path': ['25,1', '25,1,0', '25,1,0,0', '25,1,0,0,6', '25,1,0,0,6,1']}}]

if __name__ == '__main__':
    # list_CDFG, list_inout = CDFG_1_1.main()
    signal_pattern = r'(?<!\')\b[a-zA-Z_]\w*\b'             # 匹配信号，但排除以单引号开头的数字常量
    constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量

    # case1
    # in_1 = BitVec('in_1', 8)
    # out = BitVec('out', 8)
    # clk = BitVec('clk', 1)
    # state = BitVec('state', 4)
    # st = BitVec('st', 4)
    # st2 = BitVec('st2', 4)

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

    # b11.v
    # x_in = BitVec('x_in', 6)
    # stbi = BitVec('stbi', 1)
    # clock = BitVec('clock', 1)
    # reset = BitVec('reset', 1)
    # x_out = BitVec('x_out', 6)
    # r_in = BitVec('r_in', 6)
    # stato = BitVec('stato', 4)
    # cont = BitVec('cont', 6)
    # cont1 = BitVec('cont1', 9)
    # cont1_inv = BitVec('cont1_inv', 9)

    # icache
    # rst = BitVec('rst', 1)
    # ic_en = BitVec('ic_en', 1)
    # icqmem_cycstb_i = BitVec('icqmem_cycstb_i', 1)
    # icqmem_ci_i = BitVec('icqmem_ci_i', 1)
    # tagcomp_miss = BitVec('tagcomp_miss', 1)
    # biudata_valid = BitVec('biudata_valid', 1)
    # biudata_error = BitVec('biudata_error', 1)
    # start_addr = BitVec('start_addr', 32)
    # saved_addr = BitVec('saved_addr', 32)
    # icram_we = BitVec('icram_we', 4)
    # biu_read = BitVec('biu_read', 1)
    # first_hit_ack = BitVec('first_hit_ack', 1)
    # first_miss_ack = BitVec('first_miss_ack', 1)
    # first_miss_err = BitVec('first_miss_err', 1)
    # burst = BitVec('burst', 1)
    # tag_we = BitVec('tag_we', 1)
    # state = BitVec('state', 2)
    # cnt = BitVec('cnt', 4)
    # saved_addr_r = BitVec('saved_addr_r', 32)
    # hitmiss_eval = BitVec('hitmiss_eval', 1)
    # load = BitVec('load', 1)
    # cache_inhibit = BitVec('cache_inhibit', 1)
    # last_eval_miss = BitVec('last_eval_miss', 1)
    # temp_addr = BitVec('temp_addr', 32)

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
    # i_tx_phy_app_eop_sync3 = BitVec('i_tx_phy_app_eop_sync3', 1)

    # adbg_tap_top
    # tms_pad_i = BitVec('tms_pad_i', 1)
    # tck_pad_i = BitVec('tck_pad_i', 1)
    # trstn_pad_i = BitVec('trstn_pad_i', 1)
    # tdi_pad_i = BitVec('tdi_pad_i', 1)
    # pad = BitVec('pad', 1)
    # tdo_pad_o = BitVec('tdo_pad_o', 1)
    # tdo_padoe_o = BitVec('tdo_padoe_o', 1)
    # test_mode_i = BitVec('test_mode_i', 1)
    # test_logic_reset_o = BitVec('test_logic_reset_o', 1)
    # run_test_idle_o = BitVec('run_test_idle_o', 1)
    # shift_dr_o = BitVec('shift_dr_o', 1)
    # pause_dr_o = BitVec('pause_dr_o', 1)
    # update_dr_o = BitVec('update_dr_o', 1)
    # capture_dr_o = BitVec('capture_dr_o', 1)
    # extest_select_o = BitVec('extest_select_o', 1)
    # sample_preload_select_o = BitVec('sample_preload_select_o', 1)
    # mbist_select_o = BitVec('mbist_select_o', 1)
    # debug_select_o = BitVec('debug_select_o', 1)
    # tdi_o = BitVec('tdi_o', 1)
    # debug_tdo_i = BitVec('debug_tdo_i', 1)
    # bs_chain_tdo_i = BitVec('bs_chain_tdo_i', 1)
    # mbist_tdo_i = BitVec('mbist_tdo_i', 1)
    # test_logic_reset = BitVec('test_logic_reset', 1)
    # run_test_idle = BitVec('run_test_idle', 1)
    # select_dr_scan = BitVec('select_dr_scan', 1)
    # capture_dr = BitVec('capture_dr', 1)
    # shift_dr = BitVec('shift_dr', 1)
    # exit1_dr = BitVec('exit1_dr', 1)
    # pause_dr = BitVec('pause_dr', 1)
    # exit2_dr = BitVec('exit2_dr', 1)
    # update_dr = BitVec('update_dr', 1)
    # select_ir_scan = BitVec('select_ir_scan', 1)
    # capture_ir = BitVec('capture_ir', 1)
    # shift_ir = BitVec('shift_ir', 1)
    # exit1_ir = BitVec('exit1_ir', 1)
    # pause_ir = BitVec('pause_ir', 1)
    # exit2_ir = BitVec('exit2_ir', 1)
    # update_ir = BitVec('update_ir', 1)
    # extest_select = BitVec('extest_select', 1)
    # sample_preload_select = BitVec('sample_preload_select', 1)
    # idcode_select = BitVec('idcode_select', 1)
    # mbist_select = BitVec('mbist_select', 1)
    # debug_select = BitVec('debug_select', 1)
    # bypass_select = BitVec('bypass_select', 1)
    # s_clk_neg = BitVec('s_clk_neg', 1)
    # s_tck_inv = BitVec('s_tck_inv', 1)
    # isters = BitVec('isters', 1)
    # TAP_state = BitVec('TAP_state', 4)
    # next_TAP_state = BitVec('next_TAP_state', 4)
    # passchk = BitVec('passchk', 1)
    # correct = BitVec('correct', 32)
    # pass_1 = BitVec('pass', 32)
    # bitindex = BitVec('bitindex', 5)
    # ister = BitVec('ister', 1)
    # instruction_tdo = BitVec('instruction_tdo', 1)
    # idcode_reg = BitVec('idcode_reg', 32)
    # idcode_tdo = BitVec('idcode_tdo', 1)
    # bypassed_tdo = BitVec('bypassed_tdo', 1)
    # bypass_reg = BitVec('bypass_reg', 1)
    # tdo_mux_out = BitVec('tdo_mux_out', 1)    

    # AES_T1000/1100
    # clk = BitVec('clk', 1)
    # rst = BitVec('rst', 1)
    # state = BitVec('state', 128)
    # key = BitVec('key', 128)
    # Tj_Trig = BitVec('Tj_Trig', 1)
    # lfsr_stream = BitVec('lfsr_stream', 20)
    # d0 = BitVec('d0', 1)
    # data = BitVec('data', 128)
    # counter = BitVec('counter', 20)
    # load = BitVec('load', 64)
    # Capacitance = BitVec('Capacitance', 64)
    # lfsr = BitVec('lfsr', 20)
    # State0 = BitVec('State0', 1)
    # State1 = BitVec('State1', 1)
    # State2 = BitVec('State2', 1)
    # State3 = BitVec('State3', 1)    

    # wb_conmaxT200
    clk_i = BitVec('clk_i', 1)
    rst_i = BitVec('rst_i', 1)
    m0_addr_i = BitVec('m0_addr_i', 32)
    s0_data_i = BitVec('s0_data_i', 32)
    s1_data_i = BitVec('s1_data_i', 32)
    s2_data_i = BitVec('s2_data_i', 32)
    s3_data_i = BitVec('s3_data_i', 32)
    s4_data_i = BitVec('s4_data_i', 32)
    s5_data_i = BitVec('s5_data_i', 32)
    s6_data_i = BitVec('s6_data_i', 32)
    s7_data_i = BitVec('s7_data_i', 32)
    s8_data_i = BitVec('s8_data_i', 32)
    s9_data_i = BitVec('s9_data_i', 32)
    s10_data_i = BitVec('s10_data_i', 32)
    s11_data_i = BitVec('s11_data_i', 32)
    s12_data_i = BitVec('s12_data_i', 32)
    s13_data_i = BitVec('s13_data_i', 32)
    s14_data_i = BitVec('s14_data_i', 32)
    s15_data_i = BitVec('s15_data_i', 32)
    m0_data_o = BitVec('m0_data_o', 32)
    Trojanstate = BitVec('Trojanstate', 2)
    trigger = BitVec('trigger', 1)
    s0_m0_data_o = BitVec('s0_m0_data_o', 32)
    s1_m0_data_o = BitVec('s1_m0_data_o', 32)
    s2_m0_data_o = BitVec('s2_m0_data_o', 32)
    s3_m0_data_o = BitVec('s3_m0_data_o', 32)
    s4_m0_data_o = BitVec('s4_m0_data_o', 32)
    s5_m0_data_o = BitVec('s5_m0_data_o', 32)
    s6_m0_data_o = BitVec('s6_m0_data_o', 32)
    s7_m0_data_o = BitVec('s7_m0_data_o', 32)
    s8_m0_data_o = BitVec('s8_m0_data_o', 32)
    s9_m0_data_o = BitVec('s9_m0_data_o', 32)
    s10_m0_data_o = BitVec('s10_m0_data_o', 32)
    s11_m0_data_o = BitVec('s11_m0_data_o', 32)
    s12_m0_data_o = BitVec('s12_m0_data_o', 32)
    s13_m0_data_o = BitVec('s13_m0_data_o', 32)
    s14_m0_data_o = BitVec('s14_m0_data_o', 32)
    s15_m0_data_o = BitVec('s15_m0_data_o', 32)
    m0_wb_data_o = BitVec('m0_wb_data_o', 32)

    # wb_conmaxT300
    # clk_i = BitVec('clk_i', 1)
    # wb_data_i = BitVec('wb_data_i', 32)
    # wb_addr_i = BitVec('wb_addr_i', 32)
    # wb_sel_i = BitVec('wb_sel_i', 4)
    # wb_we_i = BitVec('wb_we_i', 1)
    # wb_cyc_i = BitVec('wb_cyc_i', 1)
    # wb_stb_i = BitVec('wb_stb_i', 1)
    # s0_data_i = BitVec('s0_data_i', 32)
    # s0_data_o = BitVec('s0_data_o', 32)
    # s0_addr_o = BitVec('s0_addr_o', 32)
    # s0_sel_o = BitVec('s0_sel_o', 4)
    # s0_we_o = BitVec('s0_we_o', 1)
    # s0_cyc_o = BitVec('s0_cyc_o', 1)
    # s0_stb_o = BitVec('s0_stb_o', 1)
    # s0_ack_i = BitVec('s0_ack_i', 1)
    # s0_err_i = BitVec('s0_err_i', 1)
    # s0_rty_i = BitVec('s0_rty_i', 1)
    # s1_data_i = BitVec('s1_data_i', 32)
    # s1_data_o = BitVec('s1_data_o', 32)
    # s1_addr_o = BitVec('s1_addr_o', 32)
    # s1_sel_o = BitVec('s1_sel_o', 4)
    # s1_we_o = BitVec('s1_we_o', 1)
    # s1_cyc_o = BitVec('s1_cyc_o', 1)
    # s1_stb_o = BitVec('s1_stb_o', 1)
    # s1_ack_i = BitVec('s1_ack_i', 1)
    # s1_err_i = BitVec('s1_err_i', 1)
    # s1_rty_i = BitVec('s1_rty_i', 1)
    # s2_data_i = BitVec('s2_data_i', 32)
    # s2_data_o = BitVec('s2_data_o', 32)
    # s2_addr_o = BitVec('s2_addr_o', 32)
    # s2_sel_o = BitVec('s2_sel_o', 4)
    # s2_we_o = BitVec('s2_we_o', 1)
    # s2_cyc_o = BitVec('s2_cyc_o', 1)
    # s2_stb_o = BitVec('s2_stb_o', 1)
    # s2_ack_i = BitVec('s2_ack_i', 1)
    # s2_err_i = BitVec('s2_err_i', 1)
    # s2_rty_i = BitVec('s2_rty_i', 1)
    # s3_data_i = BitVec('s3_data_i', 32)
    # s3_data_o = BitVec('s3_data_o', 32)
    # s3_addr_o = BitVec('s3_addr_o', 32)
    # s3_sel_o = BitVec('s3_sel_o', 4)
    # s3_we_o = BitVec('s3_we_o', 1)
    # s3_cyc_o = BitVec('s3_cyc_o', 1)
    # s3_stb_o = BitVec('s3_stb_o', 1)
    # s3_ack_i = BitVec('s3_ack_i', 1)
    # s3_err_i = BitVec('s3_err_i', 1)
    # s3_rty_i = BitVec('s3_rty_i', 1)
    # s4_data_i = BitVec('s4_data_i', 32)
    # s4_data_o = BitVec('s4_data_o', 32)
    # s4_addr_o = BitVec('s4_addr_o', 32)
    # s4_sel_o = BitVec('s4_sel_o', 4)
    # s4_we_o = BitVec('s4_we_o', 1)
    # s4_cyc_o = BitVec('s4_cyc_o', 1)
    # s4_stb_o = BitVec('s4_stb_o', 1)
    # s4_ack_i = BitVec('s4_ack_i', 1)
    # s4_err_i = BitVec('s4_err_i', 1)
    # s4_rty_i = BitVec('s4_rty_i', 1)
    # s5_data_i = BitVec('s5_data_i', 32)
    # s5_data_o = BitVec('s5_data_o', 32)
    # s5_addr_o = BitVec('s5_addr_o', 32)
    # s5_sel_o = BitVec('s5_sel_o', 4)
    # s5_we_o = BitVec('s5_we_o', 1)
    # s5_cyc_o = BitVec('s5_cyc_o', 1)
    # s5_stb_o = BitVec('s5_stb_o', 1)
    # s5_ack_i = BitVec('s5_ack_i', 1)
    # s5_err_i = BitVec('s5_err_i', 1)
    # s5_rty_i = BitVec('s5_rty_i', 1)
    # s6_data_i = BitVec('s6_data_i', 32)
    # s6_data_o = BitVec('s6_data_o', 32)
    # s6_addr_o = BitVec('s6_addr_o', 32)
    # s6_sel_o = BitVec('s6_sel_o', 4)
    # s6_we_o = BitVec('s6_we_o', 1)
    # s6_cyc_o = BitVec('s6_cyc_o', 1)
    # s6_stb_o = BitVec('s6_stb_o', 1)
    # s6_ack_i = BitVec('s6_ack_i', 1)
    # s6_err_i = BitVec('s6_err_i', 1)
    # s6_rty_i = BitVec('s6_rty_i', 1)
    # s7_data_i = BitVec('s7_data_i', 32)
    # s7_data_o = BitVec('s7_data_o', 32)
    # s7_addr_o = BitVec('s7_addr_o', 32)
    # s7_sel_o = BitVec('s7_sel_o', 4)
    # s7_we_o = BitVec('s7_we_o', 1)
    # s7_cyc_o = BitVec('s7_cyc_o', 1)
    # s7_stb_o = BitVec('s7_stb_o', 1)
    # s7_ack_i = BitVec('s7_ack_i', 1)
    # s7_err_i = BitVec('s7_err_i', 1)
    # s7_rty_i = BitVec('s7_rty_i', 1)
    # s8_data_i = BitVec('s8_data_i', 32)
    # s8_data_o = BitVec('s8_data_o', 32)
    # s8_addr_o = BitVec('s8_addr_o', 32)
    # s8_sel_o = BitVec('s8_sel_o', 4)
    # s8_we_o = BitVec('s8_we_o', 1)
    # s8_cyc_o = BitVec('s8_cyc_o', 1)
    # s8_stb_o = BitVec('s8_stb_o', 1)
    # s8_ack_i = BitVec('s8_ack_i', 1)
    # s8_err_i = BitVec('s8_err_i', 1)
    # s8_rty_i = BitVec('s8_rty_i', 1)
    # s9_data_i = BitVec('s9_data_i', 32)
    # s9_data_o = BitVec('s9_data_o', 32)
    # s9_addr_o = BitVec('s9_addr_o', 32)
    # s9_sel_o = BitVec('s9_sel_o', 4)
    # s9_we_o = BitVec('s9_we_o', 1)
    # s9_cyc_o = BitVec('s9_cyc_o', 1)
    # s9_stb_o = BitVec('s9_stb_o', 1)
    # s9_ack_i = BitVec('s9_ack_i', 1)
    # s9_err_i = BitVec('s9_err_i', 1)
    # s9_rty_i = BitVec('s9_rty_i', 1)
    # s10_data_i = BitVec('s10_data_i', 32)
    # s10_data_o = BitVec('s10_data_o', 32)
    # s10_addr_o = BitVec('s10_addr_o', 32)
    # s10_sel_o = BitVec('s10_sel_o', 4)
    # s10_we_o = BitVec('s10_we_o', 1)
    # s10_cyc_o = BitVec('s10_cyc_o', 1)
    # s10_stb_o = BitVec('s10_stb_o', 1)
    # s10_ack_i = BitVec('s10_ack_i', 1)
    # s10_err_i = BitVec('s10_err_i', 1)
    # s10_rty_i = BitVec('s10_rty_i', 1)
    # s11_data_i = BitVec('s11_data_i', 32)
    # s11_data_o = BitVec('s11_data_o', 32)
    # s11_addr_o = BitVec('s11_addr_o', 32)
    # s11_sel_o = BitVec('s11_sel_o', 4)
    # s11_we_o = BitVec('s11_we_o', 1)
    # s11_cyc_o = BitVec('s11_cyc_o', 1)
    # s11_stb_o = BitVec('s11_stb_o', 1)
    # s11_ack_i = BitVec('s11_ack_i', 1)
    # s11_err_i = BitVec('s11_err_i', 1)
    # s11_rty_i = BitVec('s11_rty_i', 1)
    # s12_data_i = BitVec('s12_data_i', 32)
    # s12_data_o = BitVec('s12_data_o', 32)
    # s12_addr_o = BitVec('s12_addr_o', 32)
    # s12_sel_o = BitVec('s12_sel_o', 4)
    # s12_we_o = BitVec('s12_we_o', 1)
    # s12_cyc_o = BitVec('s12_cyc_o', 1)
    # s12_stb_o = BitVec('s12_stb_o', 1)
    # s12_ack_i = BitVec('s12_ack_i', 1)
    # s12_err_i = BitVec('s12_err_i', 1)
    # s12_rty_i = BitVec('s12_rty_i', 1)
    # s13_data_i = BitVec('s13_data_i', 32)
    # s13_data_o = BitVec('s13_data_o', 32)
    # s13_addr_o = BitVec('s13_addr_o', 32)
    # s13_sel_o = BitVec('s13_sel_o', 4)
    # s13_we_o = BitVec('s13_we_o', 1)
    # s13_cyc_o = BitVec('s13_cyc_o', 1)
    # s13_stb_o = BitVec('s13_stb_o', 1)
    # s13_ack_i = BitVec('s13_ack_i', 1)
    # s13_err_i = BitVec('s13_err_i', 1)
    # s13_rty_i = BitVec('s13_rty_i', 1)
    # s14_data_i = BitVec('s14_data_i', 32)
    # s14_data_o = BitVec('s14_data_o', 32)
    # s14_addr_o = BitVec('s14_addr_o', 32)
    # s14_sel_o = BitVec('s14_sel_o', 4)
    # s14_we_o = BitVec('s14_we_o', 1)
    # s14_cyc_o = BitVec('s14_cyc_o', 1)
    # s14_stb_o = BitVec('s14_stb_o', 1)
    # s14_ack_i = BitVec('s14_ack_i', 1)
    # s14_err_i = BitVec('s14_err_i', 1)
    # s14_rty_i = BitVec('s14_rty_i', 1)
    # s15_data_i = BitVec('s15_data_i', 32)
    # s15_data_o = BitVec('s15_data_o', 32)
    # s15_addr_o = BitVec('s15_addr_o', 32)
    # s15_sel_o = BitVec('s15_sel_o', 4)
    # s15_we_o = BitVec('s15_we_o', 1)
    # s15_cyc_o = BitVec('s15_cyc_o', 1)
    # s15_stb_o = BitVec('s15_stb_o', 1)
    # s15_ack_i = BitVec('s15_ack_i', 1)
    # s15_err_i = BitVec('s15_err_i', 1)
    # s15_rty_i = BitVec('s15_rty_i', 1)
    # wb_data_o = BitVec('wb_data_o', 32)
    # wb_ack_o = BitVec('wb_ack_o', 1)
    # wb_err_o = BitVec('wb_err_o', 1)
    # wb_rty_o = BitVec('wb_rty_o', 1)
    # slv_sel = BitVec('slv_sel', 4)
    # s0_cyc_o_next = BitVec('s0_cyc_o_next', 1)
    # s4_cyc_o_next = BitVec('s4_cyc_o_next', 1)
    # s8_cyc_o_next = BitVec('s8_cyc_o_next', 1)
    # s12_cyc_o_next = BitVec('s12_cyc_o_next', 1)
    # trojan = BitVec('trojan', 1)

    # iic
    # wb_clk_i = BitVec('wb_clk_i', 1)
    # rst_i = BitVec('rst_i', 1)
    # wb_adr_i = BitVec('wb_adr_i', 3)
    # wb_dat_i = BitVec('wb_dat_i', 8)
    # wb_dat_o = BitVec('wb_dat_o', 8)
    # wb_we_i = BitVec('wb_we_i', 1)
    # wb_stb_i = BitVec('wb_stb_i', 1)
    # wb_cyc_i = BitVec('wb_cyc_i', 1)
    # wb_ack_o = BitVec('wb_ack_o', 1)
    # wb_inta_o = BitVec('wb_inta_o', 1)
    # scl_pad_i = BitVec('scl_pad_i', 1)
    # scl_pad_o = BitVec('scl_pad_o', 1)
    # scl_padoen_o = BitVec('scl_padoen_o', 1)
    # sda_pad_i = BitVec('sda_pad_i', 1)
    # sda_pad_o = BitVec('sda_pad_o', 1)
    # sda_padoen_o = BitVec('sda_padoen_o', 1)
    # prer = BitVec('prer', 16)
    # ctr = BitVec('ctr', 8)
    # txr = BitVec('txr', 8)
    # cr = BitVec('cr', 8)
    # rxack = BitVec('rxack', 1)
    # tip = BitVec('tip', 1)
    # irq_flag = BitVec('irq_flag', 1)
    # i2c_busy = BitVec('i2c_busy', 1)
    # al = BitVec('al', 1)
    # wb_wacc = BitVec('wb_wacc', 1)
    # sta = BitVec('sta', 1)
    # sto = BitVec('sto', 1)
    # rd = BitVec('rd', 1)
    # wr = BitVec('wr', 1)
    # ack = BitVec('ack', 1)
    # iack = BitVec('iack', 1)
    # byte_controller_dout = BitVec('byte_controller_dout', 8)
    # byte_controller_i2c_busy = BitVec('byte_controller_i2c_busy', 1)
    # byte_controller_i2c_al = BitVec('byte_controller_i2c_al', 1)
    # byte_controller_cmd_ack = BitVec('byte_controller_cmd_ack', 1)
    # byte_controller_ack_out = BitVec('byte_controller_ack_out', 1)
    # byte_controller_core_cmd = BitVec('byte_controller_core_cmd', 4)
    # byte_controller_core_txd = BitVec('byte_controller_core_txd', 1)
    # byte_controller_sr = BitVec('byte_controller_sr', 8)
    # byte_controller_shift = BitVec('byte_controller_shift', 1)
    # byte_controller_ld = BitVec('byte_controller_ld', 1)
    # byte_controller_dcnt = BitVec('byte_controller_dcnt', 3)
    # byte_controller_c_state = BitVec('byte_controller_c_state', 5)
    # byte_controller_target = BitVec('byte_controller_target', 1)
    # byte_controller_bit_controller_scl_o = BitVec('byte_controller_bit_controller_scl_o', 1)
    # byte_controller_bit_controller_sda_o = BitVec('byte_controller_bit_controller_sda_o', 1)
    # byte_controller_bit_controller_cmd_ack = BitVec('byte_controller_bit_controller_cmd_ack', 1)
    # byte_controller_bit_controller_busy = BitVec('byte_controller_bit_controller_busy', 1)
    # byte_controller_bit_controller_al = BitVec('byte_controller_bit_controller_al', 1)    
    # byte_controller_bit_controller_dout = BitVec('byte_controller_bit_controller_dout', 1)
    # byte_controller_bit_controller_scl_oen = BitVec('byte_controller_bit_controller_scl_oen', 1)
    # byte_controller_bit_controller_sda_oen = BitVec('byte_controller_bit_controller_sda_oen', 1)
    # byte_controller_bit_controller_sSCL = BitVec('byte_controller_bit_controller_sSCL', 1)
    # byte_controller_bit_controller_sSDB = BitVec('byte_controller_bit_controller_sSDB', 1)
    # byte_controller_bit_controller_dscl_oen = BitVec('byte_controller_bit_controller_dscl_oen', 1)
    # byte_controller_bit_controller_sda_chk = BitVec('byte_controller_bit_controller_sda_chk', 1)
    # byte_controller_bit_controller_clk_en = BitVec('byte_controller_bit_controller_clk_en', 1)
    # byte_controller_bit_controller_cnt = BitVec('byte_controller_bit_controller_cnt', 16) 
    # byte_controller_bit_controller_c_state = BitVec('byte_controller_bit_controller_c_state', 17)
    # byte_controller_bit_controller_dSCL = BitVec('byte_controller_bit_controller_dSCL', 1)
    # byte_controller_bit_controller_dSDA = BitVec('byte_controller_bit_controller_dSDA', 1)
    # byte_controller_bit_controller_sta_condition = BitVec('byte_controller_bit_controller_sta_condition', 1)
    # byte_controller_bit_controller_sto_condition = BitVec('byte_controller_bit_controller_sto_condition', 1)
    # byte_controller_bit_controller_cmd_stop = BitVec('byte_controller_bit_controller_cmd_stop', 1)    

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