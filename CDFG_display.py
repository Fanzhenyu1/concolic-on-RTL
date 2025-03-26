from math import *
import re
import os, glob
import sys
import random
import copy
import time
import psutil
import gc


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
                if line.count('begin') != line.count('end') - line.count('endcase'):
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

def main_process(flpath, pre_code):                                 # 主体处理函数
    # lines = pre_code.readlines()
    port = []
    z_block = []
    num = 0
    str_all = ''
    str_assign = ''
    str_always = ''
    file_w = 'dut.v'
    with open(flpath + file_w, "w", encoding="utf-8") as f:
        for index, line in enumerate(pre_code):                 # 逐行处理,line为str类型
            if 'assign' in line:                                # 处理赋值块
                a = assignment_process(line, num)               # 调用assignment_process函数处理赋值块,返回字典类型
                z_block.append(a)
                num += 1
                f.write(line)
                f.write('\n')
            elif 'always' in line:                              # 处理always块
                b, str_always = always_process(line, num)                   # 调用always_process函数处理always块,返回字典类型
                z_block.append(b)
                num += 1
                f.write(str_always)
                f.write('\n')
                pass
            elif 'module' in line and 'endmodule' not in line:         # 处理端口声明
                port = port_list(line)
                f.write(line)
                f.write('\n')
            elif 'input' in line or 'output' in line or 'wire' in line or 'reg' in line or 'endmodule' in line:  # 处理端口声明
                f.write(line)
                f.write('\n')
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
    str_line = str + f" $display(\"achieve node: {block}\");"
    return str_line

def if_process_1(str):                    # 处理if语句
    global block, dict_block, stack_condition
    block = block + ',1'                                    # if(condition) action;
    stack_condition.append(block)                           # if(condition) begin
    if_stack = stack_condition.copy()
    stack_kuohao = []
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
    str_line = condition + ' begin ' + f" $display(\"achieve node: {block}\");" + action + ' end'
    return str_line

def if_process_2(str):                    # 处理if语句
    global block, dict_block, stack_condition
    block = block + ',1'                                    # if(condition) action;
    stack_condition.append(block)                           # if(condition) begin
    if_stack = stack_condition.copy()
    stack_kuohao = []
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
    return 0

def else_process(str_1):                  # 处理else语句
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
    action = str_1.replace('else', '').strip()
    if_stack = stack_condition.copy()
    dict_block[block] = {'condition': condition, 'action': action, 'block_path': if_stack}
    pass
    str_line = str_1 + f" $display(\"achieve node: {block}\");"
    return str_line
def else_process_1(str_1):                  # 处理else语句
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
    action = str_1.replace('else', '').replace('end', '').strip()
    if_stack = stack_condition.copy()
    dict_block[block] = {'condition': condition, 'action': action, 'block_path': if_stack}
    str_line = str_1.split('else')[0].strip() + ' else begin ' + f" $display(\"achieve node: {block}\");" + action + ' end '
    pass
    return str_line

def else_process_2(str_1):                  # 处理else语句
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
    action = str_1.replace('else', '').strip()
    if_stack = stack_condition.copy()
    dict_block[block] = {'condition': condition, 'action': action, 'block_path': if_stack}
    pass
    return 0

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
    str_m = str
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
    str_list = str + f" $display(\"achieve node: {block}\");"
    return str_list

def else_if_process_1(str):               # 处理else if语句
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
    str_m = str.replace('else', '').replace('if', '').replace('end', '').strip()
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
    str_list = str.split('else')[0].strip() + f" else if {condition} begin " + f" $display(\"achieve node: {block}\");" + action + ' end'
    return str_list

def else_if_process_2(str):               # 处理else if语句
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
    str_m = str
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
    return 0

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

    dict_block = {}                                        # 定义字典类型，用于保存always块信息

    stack_condition.append(block)                                    # 将初始block编号压入栈中

    line_list = line.split('  ')
    line_list = list(filter(not_empty, line_list))           # 去除空白行

    condition = ''
    action = ''
    dict_block[block] = {'condition': condition, 'action': action, 'block_path': stack_condition.copy()}                     

    for i in range(len(line_list)):
        if 'always' in line_list[i] and 'begin' in line_list[i]:
            line_list[i] = line_list[i] + f" $display(\"achieve node: {block}\");"

        elif 'begin' in line_list[i] and 'end' in line_list[i] and '$display' in line_list[i]:
            continue

        elif 'if ' in line_list[i] and 'else ' not in line_list[i]:   # 处理if语句+begin
            if 'begin' in line_list[i]:
                line_list[i] = if_process(line_list[i])
            else:
                if ';' in line_list[i]:
                    line_list[i] = if_process_1(line_list[i])
                else:
                    if_process_2(line_list[i])
                    line_list[i+1] = ' begin ' + line_list[i+1] + f"$display(\"achieve node: {block}\"); end"                

        elif 'else' in line_list[i] and 'if ' not in line_list[i]:      # 处理else语句
            if 'begin' in line_list[i]:
                line_list[i] = else_process(line_list[i])
            else:
                if ';' in line_list[i]:
                    line_list[i] = else_process_1(line_list[i])
                else:
                    else_process_2(line_list[i])
                    line_list[i+1] = ' begin ' + line_list[i+1] + f"$display(\"achieve node: {block}\"); end"

        elif 'if' in line_list[i] and 'else ' in line_list[i]:
            if 'begin' in line_list[i]:
                line_list[i] = else_if_process(line_list[i])
            else:
                if ';' in line_list[i]:
                    line_list[i] = else_if_process_1(line_list[i])
                else:
                    else_if_process_2(line_list[i])
                    line_list[i+1] = ' begin ' + line_list[i+1] + f"$display(\"achieve node: {block}\"); end"

        # case语句处理较为复杂，注意verilog代码语法进入的处理分支是否对应
        elif 'case' in line_list[i] and 'end' not in line_list[i]:                       # 处理case语句
            num_case = 0
            str_case = line_list[i].replace('case', '').strip()
            block = block + ',' + str(num_case)
            block_case = copy.deepcopy(block)
            stack_condition.append(block)
            stack_condition_case = copy.deepcopy(stack_condition)
            # position_case = len(stack_condition.copy()) - 1

            pass

        elif 'endcase' in line_list[i]:                    # 处理endcase语句
            pass
        
        elif 'default' in line_list[i]:                   # default语句后紧跟赋值语句
            stack_condition = stack_condition_case.copy()
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
        elif ': ' in line_list[i] and ';' in line_list[i] :   # 处理case赋值语句
            stack_condition = stack_condition_case.copy()
            num_case += 1
            block = block_case[:-1] + str(num_case)
            stack_condition[-1] = block
            action = line_list[i].split(':')[1].strip()

            line_list[i] = line_list[i].split(':')[0] + f": begin $display(\"achieve node: {block}\"); " + action + ' end'
            pass
        elif ':' in line_list[i] and ';' not in line_list[i] and '[' not in line_list[i]:  # 处理case普通语句
        # elif ': ' in line_list[i] and ';' not in line_list[i]:  # 处理case普通语句
            stack_condition = stack_condition_case.copy()
            num_case += 1
            block = block_case[:-1] + str(num_case)
            stack_condition[-1] = block

            line_list[i+1] = line_list[i+1] + f" $display(\"achieve node: {block}\"); "
            pass

        elif '=' in line_list[i] and ';' in line_list[i]:   # 处理一般赋值语句
            dict_block[block]['action'] += line_list[i].strip()
            pass
        pass
    pass
    str_always = ''
    for i in range(len(line_list)):
        str_always += line_list[i]
    return dict_block, str_always                                      # 返回字典类型

def monitored_task():

    flpath = 'D:/mylife_yanjiu/project/concolic_on_RTL/RTL/b10/'
    file1 = 'b10_1.v'

    pre_code = code_preprocess(flpath,file1)        # 预处理verilog代码,输出list类型
    cdfg_list, inout_port = main_process(flpath, pre_code)                          # 主体处理函数,输出list类型

    # print(cdfg_list)
    return cdfg_list, inout_port


def main():

    cdfg_list, inout_port = monitored_task()
    # print(cdfg_list)
    return cdfg_list, inout_port

if __name__ == '__main__':
    main()