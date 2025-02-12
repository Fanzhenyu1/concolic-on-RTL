from math import *
import re
import target_path


dict_CDFG_inout,list_inout,path_in_block,target_path_C,target_path_D = target_path.main()


def not_empty(s):
    return s and s.strip()

def path_reduction(path_in_block,path_list):

    list_constraints = []

    ###### condition对应的约束，为块内路径条件集合 ######
    constraint_condition = []
    for i in range(len(path_in_block)):
        key_node = path_in_block[i]
        constraint_condition.append(dict_CDFG_inout[key_node]['condition'])  # 字符串列表
    constraint_condition = list(filter(not_empty, constraint_condition))  # 去除空字符串

    ###### action对应的约束，上级节点对应的操作 ######
    for i in range(len(path_list)):
        constraint_action = []
        constraint_single = []
        target_node = path_list[i][1]
        node_action = dict_CDFG_inout[target_node]['action']  # 字符串
        constraint_action.append(node_action)  # 字符串列表
        pass
        ###### 建立单条路径对应的约束 ######
        constraint_single.extend(constraint_condition)
        constraint_single.extend(constraint_action)
        ###### 构造多条路径对应的约束列表 ######
        list_constraints.append(constraint_single)
        pass
    return list_constraints

def main():
    a = path_reduction(path_in_block,target_path_C)
    print(a)
    return target_path_C, a

if __name__ == '__main__':
    main()