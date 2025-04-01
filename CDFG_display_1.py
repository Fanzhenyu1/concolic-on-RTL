from math import *
import re
import os, glob
import sys
import random
import copy
import time
import psutil
import gc
import argparse


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

def main_process(flpath, pre_code):                                 # 主体处理函数

    num = 0
    str_always = ''
    file_w = 'dut.v'
    with open(flpath + file_w, "w", encoding="utf-8") as f:
        for index, line in enumerate(pre_code):                 # 逐行处理,line为str类型
            if 'assign' in line:                                # 处理赋值块
                num += 1
                f.write(line)
                f.write('\n')
            elif 'always' in line:                              # 处理always块
                str_always = always_process(line, num)                   # 调用always_process函数处理always块
                num += 1
                f.write(str_always)
                f.write('\n')
                pass
            elif 'module' in line and 'endmodule' not in line:         # 处理端口声明
                f.write(line)
                f.write('\n')
            elif 'input' in line or 'output' in line or 'wire' in line or 'reg' in line or 'endmodule' in line:  
                f.write(line)
                f.write('\n')
            pass
        pass
    return 0

def if_process(str):                    # 处理if语句
    global block, dict_block, stack_condition
    block = block + ',1'                                    # if(condition) action;
    stack_condition.append(block)                           # if(condition) begin

    str_line = str + f" $display(\"achieve node: {block}\");"
    return str_line

def if_process_1(str):                    # 处理if语句
    global block, dict_block, stack_condition
    block = block + ',1'                                    # if(condition) action;
    stack_condition.append(block)                           # if(condition) begin
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
    str_line = condition + ' begin ' + f" $display(\"achieve node: {block}\");" + action + ' end'
    return str_line

def if_process_2(str):                    # if() \n
    global block, dict_block, stack_condition
    block = block + ',1'                                    # if(condition) action;
    stack_condition.append(block)                           # if(condition) begin
    return 0

def else_process(str_1):                  # 处理else语句
    global block, stack_condition

    if stack_condition[-1][-1] == '1':                                  # 确定else下条件编号
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
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)
    pass
    str_line = str_1 + f" $display(\"achieve node: {block}\");"
    return str_line

def else_process_1(str_1):                  # 处理else语句
    global block, stack_condition

    if stack_condition[-1][-1] == '1':                                  # 确定else下条件编号
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
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)
    action = str_1.replace('else', '').replace('end', '').strip()

    str_line = str_1.split('else')[0].strip() + ' else begin ' + f" $display(\"achieve node: {block}\");" + action + ' end '
    pass
    return str_line

def else_process_2(str_1):                  # 处理else语句
    global block, stack_condition

    if stack_condition[-1][-1] == '1':                                  # 确定else下条件编号
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
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)
    pass
    return 0

def else_if_process(str):               # 处理else if语句
    global block, stack_condition
    if stack_condition[-1][-1] == '1':                                  # 确定else下条件编号
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
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)

    ########else_if#########
    block = block + ',1'                                    # if(condition) action; 
    stack_condition.append(block)                           # if(condition) begin

    str_list = str + f" $display(\"achieve node: {block}\");"
    return str_list

def else_if_process_1(str):               # 处理else if语句
    global block, stack_condition
    if stack_condition[-1][-1] == '1':                                  # 确定else下条件编号
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

        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)

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
    str_list = str.split('else')[0].strip() + f" else if {condition} begin " + f" $display(\"achieve node: {block}\");" + action + ' end'
    return str_list

def else_if_process_2(str):               # 处理else if语句
    global block, stack_condition
    if stack_condition[-1][-1] == '1':                                  # 确定else下条件编号
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
        block = stack_condition[-1][:-1] + '0'
        stack_condition.pop()
        stack_condition.append(block)

    ########else_if#########
    block = block + ',1'                                    # if(condition) action; 
    stack_condition.append(block)                           # if(condition) begin

    return 0


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
    stack_condition_case = []
    num_case = 0

    stack_condition.append(block)                                    # 将初始block编号压入栈中

    line_list = line.split('  ')
    line_list = list(filter(not_empty, line_list))           # 去除空白行

    for i in range(len(line_list)):
        if 'always' in line_list[i] and 'begin' in line_list[i]:
            line_list[i] = line_list[i] + f" $display(\"achieve node: {block}\");"

        elif 'begin' in line_list[i] and 'end' in line_list[i] and '$display' in line_list[i] and 'case' not in line_list[i]:
            continue

        elif 'if ' in line_list[i] and 'else ' not in line_list[i]:   # 处理if语句+begin
            if 'begin' in line_list[i]:
                line_list[i] = if_process(line_list[i])
            else:
                if ';' in line_list[i]:     # if() action;
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
        elif 'case' in line_list[i] and 'endcase' not in line_list[i]:                       # 处理case语句
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

        elif 'endcase' in line_list[i]:                    # 处理endcase语句
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
            action = line_list[i].split('default:')[-1].strip()
            line_list[i] = ' default: begin ' + action + f" $display(\"achieve node: {block}\"); end"
            block = block[:-2]
            pass
        
        # elif ':' in line_list[i] and ';' in line_list[i] and '[' not in line_list[i]:   # 处理case赋值语句
        elif ': ' in line_list[i] and ';' in line_list[i] and '?' not in line_list[i] and 'display' not in line_list[i]:   # 处理case赋值语句
            stack_condition = case_stack_list[-1].copy()
            num_case += 1
            block = block_case_list[-1][:-1] + str(num_case)
            stack_condition[-1] = block
            action = line_list[i].split(':')[1].strip()
            line_list[i] = line_list[i].split(':')[0] + f": begin $display(\"achieve node: {block}\"); " + action + ' end'
            pass
        elif ':' in line_list[i] and ';' not in line_list[i] and '[' not in line_list[i]:  # 处理case普通语句
        # elif ': ' in line_list[i] and ';' not in line_list[i]:  # 处理case普通语句
            stack_condition = case_stack_list[-1].copy()
            num_case += 1
            block = block_case_list[-1][:-1] + str(num_case)
            stack_condition[-1] = block
            line_list[i+1] = ' ' + line_list[i+1] + f" $display(\"achieve node: {block}\"); "
            pass

        elif '=' in line_list[i] and ';' in line_list[i]:   # 处理一般赋值语句
            pass
        pass
    pass
    str_always = ''
    for i in range(len(line_list)):
        str_always += line_list[i]
    return str_always

def monitored_task(module_name):

    flpath = f'D:/mylife_yanjiu/project/concolic_on_RTL/RTL/{module_name}/'
    file1 = f'{module_name}_1.v'
    file2 = file1.split('.')[0] + '_preprocessed.txt'

    with open(flpath + file2, 'r') as f:
        pre_code = f.readlines()

    # pre_code = code_preprocess(flpath,file1)        # 预处理verilog代码,输出list类型
    main_process(flpath, pre_code)                          # 主体处理函数,输出list类型


    return 0


def main(module_name):

    monitored_task(module_name)

    return 0

if __name__ == '__main__':
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="CDFG Generator for Verilog HDL",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 添加必须参数
    parser.add_argument("module", 
                      type=str,
                      help="Name of the target Verilog module")
    
    # 可选参数示例
    parser.add_argument("-o", "--output",
                      default="_1_preprocessed.txt",
                      help="Output file suffix")
    
    # 解析参数
    args = parser.parse_args()

    main(module_name=args.module)