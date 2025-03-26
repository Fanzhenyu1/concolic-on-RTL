from math import *
import re
import CDFG_1_1
from z3 import *
import verilog2z3
import target_path_1_1 

list_CDFG, list_inout = CDFG_1_1.main()

select_node = ['3,1,0,1,0,0,1','1,0,0,0,0,1']
execute_node = ['1,0,0,0,0,0',
'2,1,0,0,1',
'5,1,0,1',
'4,1,0,2',
'3,1,0,4']


action_now = ['int_state:  1',
'int_assert_o: 0',
'int_addr_o:          0',
'we_o: 1',
'waddr_o:        768',
'data_o: 1696810434',
'csr_state: 16',
'cause: 2147483652']

reset_name = 'rst'
def not_empty(s):
    return s and s.strip()

def constraint_action(action_now):
    action_stack = []
    for i in range(len(action_now)):
        action_list = action_now[i].split(':')
        action = action_list[0].strip() + ' == ' + action_list[1].strip()
        action_stack.append(action)
    return action_stack

def constraint_condition(select_node, list_CDFG):

    list_CDFG_inout = []
    condition_stack = []
    for i in range(len(list_CDFG)):                # 遍历列表元素，数据类型为字典，含有一个块内的所有节点信息
        list_CDFG_inout.append(target_path_1_1.inout_extract(list_CDFG[i], reset_name))
        pass
    pass
    # print(list_CDFG_inout)
    dict_CDFG_inout = {}                           # 合并字典
    for i in list_CDFG_inout:
        dict_CDFG_inout.update(i)
        pass    

    block_path = dict_CDFG_inout[select_node[0]]['block_path']
    flag_rst = 0
    for m in range(len(block_path)):
        if reset_name not in dict_CDFG_inout[block_path[m]]['condition']:  # 排除reset信号
            condition_stack.append(dict_CDFG_inout[block_path[m]]['condition'])
            flag_rst += 1
    if flag_rst == 0:
        print(f"warning:{select_node[0]}只包含reset相关")     # 一般不会触发
    condition_stack = list(filter(not_empty, condition_stack))
    return condition_stack

action_stack = constraint_action(action_now)
print(action_stack)
condition_stack = constraint_condition(select_node, list_CDFG)
print(condition_stack)