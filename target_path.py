from math import *
import re
import os, glob
import sys
import random
import copy
import subprocess
import CDFG_1

# result_CDFG = subprocess.run(['python', 'd:\mylife_yanjiu\project\RTL-Contest\CDFG_1.py'], stdout=subprocess.PIPE)
# rtl_CDFG = result_CDFG.stdout.decode('utf-8')
list_CDFG, list_inout = CDFG_1.main()

def not_empty(s):
    return s and s.strip()

def inout_extract(dict_block):                  # 提取条件与操作中的输入输出信号，便于路径生成
    for key, value in dict_block.items():       # value为字典，含有条件、操作、块内路径信息
        str_condition = value['condition']
        str_action = value['action']
        action_list = str_action.split(';')
        action_list = list(filter(not_empty, action_list))
        ##确定分隔符##
        list_condition = re.split(r"[!&()*+<=>| \-]+", str_condition)
        pass
        list_condition = list(filter(not_empty, list_condition))
        action_in = []
        action_out = []
        if str_action != '':
            for action_one in action_list:
                action_out.append(action_one.strip().split(' ')[0])
                action_instr = action_one.split('=')[1]
                action_inlist = re.split(r"[!&()*+| \-]+", action_instr)
                action_inlist = list(filter(not_empty, action_inlist))
                for item in action_inlist:
                    action_in.append(item)
        else:
            action_in = []
            action_out = []
        value['action_in'] = action_in
        value['action_out'] = action_out
        value['condition_in'] = list_condition
        
        pass
    pass
    return dict_block

def main():
    list_CDFG_inout = []
    for i in range(len(list_CDFG)):                # 遍历列表元素，数据类型为字典，含有一个块内的所有节点信息
        list_CDFG_inout.append(inout_extract(list_CDFG[i]))
        pass
    pass
    # print(list_CDFG_inout)
    dict_CDFG_inout = {}                           # 合并字典
    for i in list_CDFG_inout:
        dict_CDFG_inout.update(i)
        pass
    print(dict_CDFG_inout)                        # 输出模块所有节点信息
    print(list_inout)                             # 输出模块所有输入输出信号列表

    
    pass
    return dict_CDFG_inout, list_inout

if __name__ == '__main__':
    main()
    pass