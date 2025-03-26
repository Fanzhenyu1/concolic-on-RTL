from math import *
import re
import os, glob
import sys
import random
import copy
import time
import psutil
import gc
from threading import Thread, Event


# 监控模块
class MemoryMonitor(Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = Event()
        self.peak_memory = 0  # 单位：MB
        self.process = psutil.Process(os.getpid())
        self.ready_event = Event()  # 新增准备就绪信号

    def _get_current_memory(self):
        """获取当前进程内存使用量"""
        return self.process.memory_info().rss / 1024  # 转换为MB

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


def code_preprocess(flpath,file1):                  # 预处理verilog代码
    file2 = file1.split('.')[0] + '_preprocessed.txt'
    processed_lines = []

    # with open(flpath + file1, encoding='utf-8') as f1:
    with open(flpath + file1) as f1:
        lines = f1.readlines()
        for index, line in enumerate(lines):
            # line = line.replace("  ", " ")           # 去除多余空格
            line = re.sub(r" {2,}", " ", line)         # 合并连续空格
            if '//' in line:                        # 去除文本中的注释
                line = line.split('//')[0].strip()
            if line == '\n':                        # 去除多余空行
                line = line.replace('\n', '')
            # line = re.sub(r"  ", " ", line)       # 去除多余空格
            while 'module' in line and 'endmodule' not in line:  # 处理模块声明
                if line.count('(')!= line.count(')'):
                    line = line.split('//')[0].strip()
                    line = line.replace('\n', ' ')
                    index = index + 1
                    line += lines[index]
                    lines[index] = ''
                    continue
                else:
                    break
            while 'always ' in line:                # 处理always块，使其只有一行
                if 'begin' not in line:
                    line = line.split('//')[0].strip() + '\n'
                    line = line.replace('\n', '  ')
                    index = index + 1
                    # line += lines[index].replace('  ', ' ')
                    lines[index] = re.sub(r" {2,}", " ", lines[index])
                    line = line + lines[index]
                    lines[index] = '' 
                    continue   
                if line.count('begin') != line.count(' end') - line.count('endcase'):
                    line = line.split('//')[0].strip() + '\n'
                    line = line.replace('\n', '  ')
                    index = index + 1
                    # line += lines[index].replace('  ', ' ')
                    lines[index] = re.sub(r" {2,}", " ", lines[index])
                    line = line + lines[index]
                    lines[index] = ''
                    continue
                
                else:
                    break
            processed_lines.append(line)
        with open(flpath + file2, 'w') as f2:       # 保存处理后的verilog代码
            f2.writelines(processed_lines)

    return processed_lines                          # 返回处理后的verilog代码，数据类型为list

def main_process(pre_code):                                 # 主体处理函数
    # lines = pre_code.readlines()
    port = []
    z_block = []
    num = 0
    for index, line in enumerate(pre_code):                 # 逐行处理,line为str类型
        if 'assign' in line:                                # 处理赋值块
            a = assignment_process(line, num)               # 调用assignment_process函数处理赋值块,返回字典类型
            z_block.append(a)
            num += 1
        elif 'always' in line:                              # 处理always块
            b = always_process(line, num)                   # 调用always_process函数处理always块,返回字典类型
            z_block.append(b)
            num += 1
            pass
        elif 'module' in line and 'endmodule' not in line:         # 处理端口声明
            port = port_list(line)
        pass
    pass
    return z_block, port

def port_list(line):
    list_port = re.split(r'[(),;]+', line.replace(' ', ''))
    list_port = list(filter(not_empty, list_port))
    list_port = list_port[1:]
    pass
    return  list_port

def if_process(str):                    # 处理if语句
    global block, dict_block, stack_condition
    block = block + ',1'                                    # if(condition) action;
    stack_condition.append(block)                           # if(condition) begin
    if_stack = stack_condition.copy()
    stack_kuohao = []
    str = str.replace('if ', ' ')
    for j in range(len(str)):
        if str[j] == '(':
            stack_kuohao.append(j)
        elif str[j] == ')':
            stack_kuohao.pop()
            if stack_kuohao == []:
                condition = str[0:j+1].strip()
                action = str[j+1:].strip()
                break
    if not any(op in condition for op in ('=', '^', '>', '<', "'", "&&", "||", "&(", "|(")):
        condition = condition + " == 1'b1"

    dict_block[block] = {'condition': condition, 'action': action, 'block_path': if_stack}
    return block, stack_condition, dict_block[block]

def else_process(str):                  # 处理else语句
    global block, dict_block, stack_condition

    if stack_condition[-1][-1] == '1':                                  # 确定else下条件编号
        condition = dict_block[block]['condition']
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)
    else:
        len_2 = len(stack_condition)
        for j in range(1,len_2):
            if stack_condition[-j-1][-1] == '1':
                break
        for k in range(j):
            stack_condition.pop()
        condition = dict_block[stack_condition[-1]]['condition']
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)
    condition = '!' + condition                    # else action; 
    action = str.replace('else', '').strip()
    if_stack = stack_condition.copy()
    dict_block[block] = {'condition': condition, 'action': action, 'block_path': if_stack}
    pass
    return block, stack_condition, dict_block

def else_if_process(str):               # 处理else if语句
    global block, dict_block, stack_condition
    if stack_condition[-1][-1] == '1':                                  # 确定else下条件编号
        condition = dict_block[block]['condition']
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)
    else:
        len_1 = len(stack_condition)
        for j in range(1,len_1):
            if stack_condition[-j-1][-1] == '1':
                break
        for k in range(j):
            stack_condition.pop()
        condition = dict_block[stack_condition[-1]]['condition']
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)
    condition = '!' + condition                    # else action;
    if_stack = stack_condition.copy()
    dict_block[block] = {'condition': condition, 'action': '', 'block_path': if_stack}
    ########else_if#########
    block = block + ',1'                                    # if(condition) action; 
    stack_condition.append(block)                           # if(condition) begin
    stack_kuohao = []
    str_m = str.replace('if ', ' ').replace('else', '')
    m = len(str_m)
    for j in range(m):
        if str_m[j] == '(':
            stack_kuohao.append(j)
        elif str_m[j] == ')':
            stack_kuohao.pop()
            if stack_kuohao == []:
                condition = str_m[0:j+1].strip()
                action = str_m[j+1:].strip()
                break
    if_stack = stack_condition.copy()
    if not any(op in condition for op in ('=', '^', '>', '<', "'", "&&", "||", "&(", "|(")):
        condition = condition + " == 1'b1"
    dict_block[block] = {'condition': condition, 'action': action, 'block_path': if_stack}
    return block, stack_condition, dict_block

def case_process():
    pass
    return

def assignment_process(line, num):                         # 处理赋值块,line为str类型
    block = str(num) + ',0'
    dict_assign = {}
    stack_condition = []
    stack_condition.append(block)
    # 正则表达式匹配 assign 语句
    pattern = re.compile(r"assign\s+(\w+)\s*=\s*\((.*?)\)\s*\?\s*(.*?)\s*:\s*(.*?);")

    match = pattern.search(line)
    if match:
        output_signal = match.group(1)        # 输出信号
        condition = match.group(2)            # 条件表达式
        true_value = match.group(3)           # 条件为真时赋值
        false_value = match.group(4)          # 条件为假时赋值

        # 条件为真时的节点信息
        block = block + ',1'
        stack_condition.append(block)
        action_true = output_signal + ' = ' + true_value + ';'
        dict_assign[block] = {'condition': condition, 'action': action_true, 'block_path': stack_condition.copy()}

        # 条件为假时的节点信息
        block = block[:-1] + '0'
        stack_condition[-1] = block
        action_false = output_signal + ' = ' + false_value + ';'
        condition = '!' + '(' + condition + ')'
        dict_assign[block] = {'condition': condition, 'action': action_false, 'block_path': stack_condition.copy()}
    else:
        pattern = re.compile(r"assign\s+(\w+)\s*=\s*(.*?);")
        match = pattern.search(line)
        if match:
            output_signal = match.group(1)        # 输出信号
            action = output_signal + ' = ' + match.group(2) + ';'      # 赋值表达式            
            dict_assign[block] = {'condition': '', 'action': action, 'block_path': stack_condition.copy()}
    pass
    return dict_assign                                                 # 返回字典类型

def not_empty(s):
    return s and s.strip()

def always_process(line, num):                             # 处理always块,line为str类型
    global block, dict_block, stack_condition

    block = ''                                             
    # block格式，如'0,0,1,1'表示第0块，组合逻辑，第一第二条件均为true
    if 'posedge' in line:                                  # 初始block编号，1表示时序逻辑，0表示组合逻辑
        block = str(num) + ',1'
    else:
        block = str(num) + ',0'

    stack_condition = []                                   # 定义栈类型，用于保存条件路径信息
    case_stack_list = []
    block_case_list = []
    case_num_list = []
    str_case_list = []

    dict_block = {}                                        # 定义字典类型，用于保存always块信息
    block_case = ''
    stack_condition.append(block)                                    # 将初始block编号压入栈中
    # 构建分割后的结果列表
    line_list = line.replace('begin', '')
    line_list = re.sub(r'end(?!case)', '', line_list)
    line_list = line_list.split('  ')
    # line_list = line.split('  ')                           # 将always块切片，分割为列表

    line_list = list(filter(not_empty, line_list))           # 去除空白行


    condition = ''
    action = ''
    # signal_in = ''
    # signal_out = ''
    block_path = ''
    dict_block[block] = {'condition': condition, 'action': action, 'block_path': stack_condition.copy()}                     
    # 字典初始化，字典元素，'0,0':{'condition': 'null', 'action': 'null','signal_in': 'null','signal_out': 'null'},字典嵌套组成sub-CDFG
    for i in range(len(line_list)):
        if 'if ' in line_list[i] and 'else ' not in line_list[i]:   # 处理if语句
            if_process(line_list[i])

        elif 'else' in line_list[i] and 'if ' not in line_list[i]:      # 处理else语句
            else_process(line_list[i])

        elif 'if' in line_list[i] and 'else ' in line_list[i]:
            else_if_process(line_list[i])

        elif 'case' in line_list[i] and 'end' not in line_list[i]:                       # 处理case语句
            
            if block_case_list != []:
                case_num_list.append(num_case)
                block = block_case[:-1] + str(num_case)

            num_case = 0
            ## block 为当前节点编号
            block = block + ',' + str(num_case)
            ## stack_condition 为当前节点的块内路径
            stack_condition.append(block)

            ## 剥离出case条件控制信号
            str_case = line_list[i].replace('case', '').strip()
            str_case_list.append(str_case)
            ## 
            block_case = copy.deepcopy(block)
            
            stack_condition_case = copy.deepcopy(stack_condition)

            # position_case = len(stack_condition.copy()) - 1

            block_case_list.append(block_case)
            case_stack_list.append(stack_condition_case)
            pass

        elif  'endcase' in line_list[i]:                    # 处理endcase语句
            block = block_case_list[-1]
            block = block[:-2]
            if case_num_list != []:
                num_case = case_num_list[-1]
                case_num_list.pop()
            case_stack_list.pop()
            block_case_list.pop()
            str_case_list.pop()
            pass
        
        elif 'default' in line_list[i]:                   # default语句后紧跟赋值语句
            stack_condition = case_stack_list[-1].copy()
            
            num_case += 1
            block = block_case[:-1] + str(num_case)
            
            stack_condition[-1] = block
            # stack_condition = stack_condition
            case_stack1 = stack_condition.copy()
            condition = 'default'
            # action = line_list[i].split(':')[-1].strip()
            action = line_list[i].split('default:')[-1].strip()
            dict_block[block] = {'condition': condition, 'action': action, 'block_path': case_stack1}
            block = block[:-2]
            pass
        # elif ':' in line_list[i] and ';' in line_list[i] and '[' not in line_list[i]:   # 处理case赋值语句
        elif ': ' in line_list[i] and ';' in line_list[i] and '?' not in line_list[i]:   # 处理case赋值语句
            stack_condition = case_stack_list[-1].copy()
            num_case += 1
            block = block_case_list[-1][:-1] + str(num_case)
            stack_condition[-1] = block
            # stack_condition = stack_condition
            case_stack2 = stack_condition.copy()
            condition = str_case_list[-1] + ' == ' + line_list[i].split(':')[0].strip()
            action = line_list[i].split(':')[1].strip()
            dict_block[block] = {'condition': condition, 'action': action, 'block_path': case_stack2}
            pass
        elif ':' in line_list[i] and ';' not in line_list[i] and '[' not in line_list[i]:  # 处理case普通语句
        # elif ': ' in line_list[i] and ';' not in line_list[i]:  # 处理case普通语句
            stack_condition = case_stack_list[-1].copy()
            num_case += 1
            block = block_case_list[-1][:-1] + str(num_case)
            stack_condition[-1] = block
            # stack_condition = stack_condition
            case_stack3 = stack_condition.copy()
            condition = str_case_list[-1] + ' == ' + line_list[i].split(':')[0].strip()
            dict_block[block] = {'condition': condition, 'action': '', 'block_path': case_stack3}
            pass

        elif '=' in line_list[i] and ';' in line_list[i]:   # 处理一般赋值语句
            dict_block[block]['action'] += line_list[i].strip()
            pass
        pass
    pass
    return dict_block                                      # 返回字典类型

def monitored_task():
    # default语句处理存在bug，待修复
    # flpath = 'D:/mylife_yanjiu/project/concolic_on_RTL/RTL/core/clint/'
    # file1 = 'clint.v'


    # flpath = 'D:/mylife_yanjiu/project/concolic_on_RTL/RTL/RS232-T400/'
    # file1 = 'uart_top copy.v'

    # flpath = 'D:/mylife_yanjiu/project/concolic_on_RTL/RTL/usb_phy/'
    # file1 = 'usb_phy_1.v'
    # pre_code = code_preprocess(flpath,file1)        # 预处理verilog代码,输出list类型
    # cdfg_list, inout_port = main_process(pre_code)                          # 主体处理函数,输出list类型

    flpath = 'D:/mylife_yanjiu/project/concolic_on_RTL/RTL/case3/'
    file1 = 'case3.v'
    pre_code = code_preprocess(flpath,file1)        # 预处理verilog代码,输出list类型
    cdfg_list, inout_port = main_process(pre_code)                          # 主体处理函数,输出list类型

    print(cdfg_list)
    return cdfg_list, inout_port


def main():
    # 垃圾回收
    for _ in range(3):
        gc.collect()
    monitor = MemoryMonitor()
    monitor.start()
    monitor.ready_event.wait()
    start_time = time.time()

    cdfg_list, inout_port = monitored_task()

    monitor.stop()
    # monitor.join()
    end_time = time.time()
    execution_time = end_time - start_time
    gc.collect()
    print("Execution time in seconds: ", execution_time)
    print(f"峰值内存占用：{monitor.peak_memory:.2f} KB")
    return cdfg_list, inout_port

if __name__ == '__main__':
    main()