from math import *
import re
import os, glob
import sys
import random
import copy

def code_preprocess(flpath,file1):                  # 预处理verilog代码
    file2 = file1.split('.')[0] + '_preprocessed.txt'
    processed_lines = []
    stack = []

    with open(flpath + file1) as f1:
        lines = f1.readlines()
        for index, line in enumerate(lines):
            line = re.sub(r"  ", " ", line)           # 去除多余空格
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
                else:
                    break
            while 'always ' in line:                # 处理always块，使其只有一行
                if line.count('begin') != line.count('end') - line.count('endcase'):
                    line = line.split('//')[0].strip()
                    line = line.replace('\n', ' ')
                    index = index + 1
                    line += lines[index].replace('  ', ' ')
                    lines[index] = ''
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
    for index, line in enumerate(pre_code):                    # 逐行处理,line为str类型
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
    condition = condition + '!'                    # else action; 
    action = str.replace('else', '').strip()
    if_stack = stack_condition.copy()
    dict_block[block] = {'condition': condition, 'action': action, 'block_path': if_stack}
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
    condition = condition + '!'                    # else action;
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
    assign_line = line.replace('assign', '').strip()
    assign_out = assign_line.split('=')[0].strip()
    assign_in = assign_line.split('=')[1].strip()
    assign_in_list = re.split(r'[?:&|!~^+-/()0;]', assign_in)
    assign_in_list = list(filter(not_empty, assign_in_list))
    if '?' in assign_in and ':' in assign_in:
        dict_assign[block] = {'condition': '', 'action': '', 'block_path': stack_condition.copy()}
        in_list = re.split(r'[?:]', assign_in)              # 处理三目运算符
        block = block + ',1'
        condition = in_list[0].strip()
        action = assign_out + '=' +in_list[1].strip()
        stack_condition.append(block)
        assign_path = stack_condition.copy()
        # dict_assign[block] = {'condition': condition, 'action': action, 'signal_in': assign_in_list, 'signal_out': assign_out, 'block_path': assign_path}
        dict_assign[block] = {'condition': condition, 'action': action, 'block_path': assign_path}
        block = block[:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)
        condition = condition + '!'
        action = assign_out + '=' + in_list[2].strip()
        assign_path = stack_condition.copy()
        # dict_assign[block] = {'condition': condition, 'action': action, 'signal_in': assign_in_list, 'signal_out': assign_out, 'block_path': assign_path}
        dict_assign[block] = {'condition': condition, 'action': action, 'block_path': assign_path}
    else:
        assign_action = assign_line
        # dict_assign[block] = {'condition': '', 'action': assign_line, 'signal_in': assign_in_list, 'signal_out': assign_out, 'block_path': [block]}
        dict_assign[block] = {'condition': '', 'action': assign_line, 'block_path': [block]}
        pass
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
    stack = []                                             # 定义栈类型，用于保存begin信息
    stack_condition = []                                   # 定义栈类型，用于保存条件路径信息
    stack_kuohao = []                                      # 定义栈类型，用于计算括号匹配
    dict_block = {}                                        # 定义字典类型，用于保存always块信息

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

        elif 'else ' in line_list[i] and 'if ' not in line_list[i]:      # 处理else语句
            else_process(line_list[i])

        elif 'if ' in line_list[i] and 'else ' in line_list[i]:
            else_if_process(line_list[i])

        # elif line_list[i] == 'begin':                      # 处理begin语句
        #     pass

        # elif line_list[i] == 'end':                        # 处理end语句
        #     pass

        elif 'case' in line_list[i] and 'end' not in line_list[i]:                       # 处理case语句
            num_case = 0
            str_case = line_list[i].replace('case', '').strip()
            block = block + ',' + str(num_case)
            block_case = copy.deepcopy(block)
            stack_condition.append(block)
            stack_condition_case = copy.deepcopy(stack_condition)
            # position_case = len(stack_condition.copy()) - 1

            pass

        elif line_list[i] == 'endcase':                    # 处理endcase语句
            pass
        
        elif 'default' in line_list[i]:
            stack_condition = stack_condition_case.copy()
            num_case = 0
            block = block_case[:-1] + str(num_case)
            stack_condition[-1] = block
            # stack_condition = stack_condition
            case_stack1 = stack_condition.copy()
            condition = 'default'
            action = line_list[i].split(':')[-1].strip()
            dict_block[block] = {'condition': condition, 'action': action, 'block_path': case_stack1}
            pass

        elif ':' in line_list[i] and ';' in line_list[i]:   # 处理case赋值语句
            stack_condition = stack_condition_case.copy()
            num_case += 1
            block = block_case[:-1] + str(num_case)
            stack_condition[-1] = block
            # stack_condition = stack_condition
            case_stack2 = stack_condition.copy()
            condition = str_case + ' == ' + line_list[i].split(':')[0].strip()
            action = line_list[i].split(':')[1].strip()
            dict_block[block] = {'condition': condition, 'action': action, 'block_path': case_stack2}
            pass
        
        elif ':' in line_list[i] and ';' not in line_list[i]:
            stack_condition = stack_condition_case.copy()
            num_case += 1
            block = block_case[:-1] + str(num_case)
            stack_condition[-1] = block
            # stack_condition = stack_condition
            case_stack3 = stack_condition.copy()
            condition = str_case + ' == ' + line_list[i].split(':')[0].strip()
            dict_block[block] = {'condition': condition, 'action': '', 'block_path': case_stack3}
            pass

        elif '=' in line_list[i] and ';' in line_list[i]:   # 处理一般赋值语句
            dict_block[block]['action'] += line_list[i].strip()
            pass
        pass
    return dict_block                                      # 返回字典类型

def main():
    # flpath = 'D:/mylife_yanjiu/project/hackdac_2018_beta/ips/jtag_pulp/src/'
    # flpath = 'D:/mylife_yanjiu/project/hackdac_2018_beta/ips/adv_dbg_if/rtl/'
    flpath = 'D:/mylife_yanjiu/project/RTL-Contest/verilog-test/'
    # file1 = 'tap_top.v'
    # file1 = 'adbg_tap_top.v'
    file1 = 'case2.v'
    pre_code = code_preprocess(flpath,file1)        # 预处理verilog代码,输出list类型
    cdfg_list, inout_port = main_process(pre_code)                          # 主体处理函数,输出list类型
    
    # print(cdfg_list)
    return cdfg_list, inout_port

if __name__ == '__main__':
    main()