from math import *
import re
import os, glob
import sys
import random
import copy
import subprocess
import CDFG_1
from z3 import *
import verilog2z3
# result_CDFG = subprocess.run(['python', 'd:\mylife_yanjiu\project\RTL-Contest\CDFG_1.py'], stdout=subprocess.PIPE)
# rtl_CDFG = result_CDFG.stdout.decode('utf-8')
list_CDFG, list_inout = CDFG_1.main()
signal_pattern = r'(?<!\')\b[a-zA-Z_]\w*\b'             # 匹配信号，但排除以单引号开头的数字常量
constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量

def not_empty(s):
    return s and s.strip()

def inout_extract(dict_block, reset_name):                  # 提取条件与操作中的输入输出信号，便于路径生成
    # constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量
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

def path_generate(dict_CDFG_inout, target_node_list):
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
    node_action_out = dict_target_node['action_out']
    # node_condition_in = dict_target_node['condition_in']

    ############## 构造控制依赖信号列表 ########
    ctr_dep_list = []
    for node in path_in_block:
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
            pc,pd = path_generate(dict_CDFG_inout, [target_node_up])
            target_path_up = pc + pd

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
                pc,pd = path_generate(dict_CDFG_inout, [target_path[1]])
                path_2 = pc + pd
                pass
                search_p(dict_CDFG_inout, path_2, reset_name)
            else:
                print(f"当前路径约束下无解,该路径跳过")
                num_all += 1
                constraint_stack = constraint_stack[:-1]  # 回溯
                continue
            continue      
        else:  # 控制流路径
            if flag > 0:
                constraint_stack = constraint_stack[:-1]  # 回溯
                num_start -= 1
                flag = 0
            continue


    return 0


def main():
    # 输入reset信号名
    # reset_name = input('请输入reset信号名：')
    reset_name = 'rst'

    # 全局变量
    global num_all
    global num_apt
    global path_list
    global constraint_stack
    global flag
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


    # 路径生成
    # target_node = input('请输入目标节点：')        # 输入选择目标节点
    target_node = '2,0,3'
    path_in_block = dict_CDFG_inout[target_node]['block_path']
    print(f"目标节点块内路径：{path_in_block}")
    target_node_list = []
    target_node_list.append(target_node)             # 定义目标节点堆栈，第一个目标节点入栈
    target_path_C,target_path_D = path_generate(dict_CDFG_inout, target_node_list)         # 带递归
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
    return dict_CDFG_inout,list_inout,path_in_block,target_path_C,target_path_D

# in_1 = BitVec('in_1', 8)
# clk = BitVec('clk', 1)
# rst = BitVec('rst', 1)
# out = BitVec('out', 8)
# state = BitVec('state', 4)
# st = BitVec('st', 4)
# st2 = BitVec('st2', 4)

clk = BitVec('clk', 1)
W_in = BitVec('W_in', 1)
A_in = BitVec('A_in', 1)
sensor = BitVec('sensor', 1)
motor = BitVec('motor', 1)
next_state = BitVec('next_state', 2)
state = BitVec('state', 2)

# 定义全局变量，用于体现路径约减的效果
num_all = 0
num_apt = 0
path_list = []
constraint_stack = []
num_start = 2  # 起始优先级
flag = 0  # 用于控制路径搜索的回溯
if __name__ == '__main__':
    main()
    pass