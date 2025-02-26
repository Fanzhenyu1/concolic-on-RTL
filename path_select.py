from math import *
from z3 import *
import re
import copy

path_specification = [['3,1,0,1', '1,0', '1', '1'],['1,0', '0,0', '0', '0'],['0,0', '2,1,0,0,0,1', '0', '0'],['2,1,0,0,0,1', '2,1,0,0,1', '1', '1'],['2,1,0,0,1', '2,1,0,1', '1', '1']]

target_node = ['3,1,0,1']
execute_node_l = ['3,1,0,0', '2,1,0,0,0,1', '0,0', '1,0']

path_target_priority = [['3,1,0,1', '1,0', '1', '1', 0],['1,0', '0,0', '0', '0', 1],['0,0', '2,1,0,0,0,1', '0', '0', 2],['2,1,0,0,0,1', '2,1,0,0,1', '1', '1', 3],['2,1,0,0,1', '2,1,0,1', '1', '1', 4]]
execute_node = ['1,0']


path_priority = 0


def not_empty(s):
    return s and s.strip()

def find_elements(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    return list(set1.intersection(set2))

def node_upsearch(path_specification, execute_node):        # execute_node is a list, return a list of nodes
    up_search_nodelist = execute_node
    inter_num = 0
    for i in range(len(path_specification)):
        if path_specification[i][0] == up_search_nodelist[-1]:
            inter_num += 1
            pass            
            if path_specification[i][3] == '0':
                up_search_nodelist.append(path_specification[i][1])
                return node_upsearch(path_specification, up_search_nodelist)
            elif path_specification[i][3] == '1':
                return up_search_nodelist
    if inter_num == 0:
        return up_search_nodelist


def priority_add(path_specification, target_node, path_priority):
    num = 0
    target_node_add = []

    for i in range(len(target_node)):
        for j in range(len(path_specification)):
            if path_specification[j][0] == target_node[i]:
                path_specification[j].append(copy.deepcopy(path_priority))
                target_node_add.append(copy.deepcopy(path_specification[j][1]))
                num += 1

    for i in range(len(target_node_add)):        # remove duplicate target_node
        for j in range(len(target_node)):
            if target_node_add[i] == target_node[j]:
                target_node_add[i] = ''

    target_node = list(filter(not_empty, target_node_add))     # update target_node
    target_node = list(set(target_node))
    path_priority += 1               # update path_priority
    pass
    if num == 0:                    # avoid infinite loop
        return path_specification
    else:
        return priority_add(path_specification, target_node, path_priority)

def roll_poll(path_specification):
    # 添加轮询参数
    for i in range(len(path_specification)):
        path_specification[i].append(0)
    return path_specification

def node_select(path_specification, execute_node_l, num_poll=0):


    # confirm execution node is crucial node
    flag_error = 0
    crucial_node = []
    search_node_list = []
    for i in range(len(execute_node_l)):
        for j in range(len(path_specification)):
            pass
            if path_specification[j][1] == execute_node_l[i] and path_specification[j][3] == '1':                
                search_node_list = node_upsearch(path_specification, [execute_node_l[i]])   
                pass
                if search_node_list is not None:             
                    node_intersection = find_elements(search_node_list, execute_node_l)
                    pass
                    if set(node_intersection) == set(search_node_list):
                        flag_error = flag_error + 1
                        crucial_node.append(copy.deepcopy(path_specification[j][1]))
                        pass
    if flag_error == 0:
        print("$ERROR: the current execution node is not in path_specification or all blocks are combinatorial")
        return 0

    pass
    # for each crucial node, select the path with the highest priority, now is only one, may be changed
    # crucial node 是执行节点的子集，剔除了容易干扰的数据流相关节点
    selected_path = []
    priority_node = 512

    flag_num = 0
    for i in range(len(crucial_node)):
        for j in range(len(path_specification)):
            if path_specification[j][1] == crucial_node[i] and int(path_specification[j][4]) <= priority_node:
                
                if path_specification[j][-1] < num_poll:
                    path_specification[j][-1] += 1
                    num_poll = int(path_specification[j][-1])
                    flag_num += 1
                    
                    selected_path = path_specification[j]
                    priority_node = int(path_specification[j][4])
                    next_node = selected_path[0]
                    pass
                    return next_node, path_specification, num_poll

    if flag_num == 0:
        num_poll += 1
        return node_select(path_specification, execute_node_l, num_poll)

    # select the next node after the nearest node
    next_node = selected_path[0]
    pass
    return next_node, path_specification, num_poll


#####case1
path_specification1 = [
    ['3,1,0,1', '1,0', '1', '1', 0], ['1,0', '0,0', '0', '0', 1], ['0,0', '2,1,0,0,0,1', '0', '0', 2],
    ['2,1,0,0,0,1', '2,1,0,0,1', '1', '1', 3],
    ['2,1,0,0,1', '2,1,0,1', '1', '1', 4]
]
target_node1 = ['3,1,0,1']
execute_node_l1 = ['3,1,0,0', '2,1,0,0,1', '0,0', '1,0']

#####case4
path_specification4 = [['2,0,3', '0,1', '1', '0', 0], ['0,1', '1,0,2,0,1', '0', '1', 1], ['0,1', '1,0,3,1', '0', '1', 1], ['0,1', '1,0,3,0,0', '0', '1', 1],['1,0,2,0,1', '0,1', '1', '0', 2], ['0,1', '1,0,1,0,1', '0', '1', 3], ['0,1', '1,0,2,0,0', '0', '1', 3],['1,0,3,1', '0,1', '1', '0', 2],['1,0,3,0,0', '0,1', '1', '0', 2],['1,0,1,0,1', '0,1', '1', '0', 4], ['0,1', '1,0,1,1', '0', '1', 5], ['0,1', '1,0,1,0,0', '0', '1', 5], ['0,1', '1,0,2,1', '0', '1', 5], ['0,1', '1,0,3,0,1', '0', '1', 5], ['0,1', '1,0,4', '0', '1', 5],['1,0,2,0,0', '0,1', '1', '0', 4],['1,0,1,1', '0,1', '1', '0', 6], ['1,0,1,0,0', '0,1', '1', '0', 6], ['1,0,2,1', '0,1', '1', '0', 6], ['1,0,3,0,1', '0,1', '1', '0', 6]]
target_node4 = ['2,0,3']
execute_node_l4 = ['0,1', '1,0,1,0,0', '2,0,1']

#####clint
path_specification5 = [['5,1,0,2', '3,1,0,1,0,0,1', '1', '1', 0],
    ['3,1,0,1,0,0,1', '1,0,0,0,0,1', '1', '1', 1], ['3,1,0,1,0,0,1', '3,1,0,4', '1', '1', 1], ['3,1,0,1,0,0,1', '3,1,0,5', '1', '1', 1], ['3,1,0,1,0,0,1', '3,1,0,6', '1', '1', 1],
        ['3,1,0,4', '3,1,0,3', '1', '1', 2],
        ['3,1,0,5', '3,1,0,1,0,0,1', '1', '1', 2],
            ['3,1,0,3', '3,1,0,2', '1', '1', 3],
                ['3,1,0,2', '3,1,0,1,1', '1', '1', 4], ['3,1,0,2', '3,1,0,1,0,1', '1', '1', 4],
                    ['3,1,0,1,1', '1,0,0,1,1', '1', '1', 5], ['3,1,0,1,1', '3,1,0,4', '1', '1', 5], ['3,1,0,1,1', '3,1,0,5', '1', '1', 5], ['3,1,0,1,1', '3,1,0,6', '1', '1', 5],
                    ['3,1,0,1,0,1', '1,0,0,0,1', '1', '1', 5], ['3,1,0,1,0,1', '3,1,0,4', '1', '1', 5], ['3,1,0,1,0,1', '3,1,0,5', '1', '1', 5], ['3,1,0,1,0,1', '3,1,0,6', '1', '1', 5]
]
target_node5 = ['5,1,0,2']
execute_node_l5 = ['1,0,0,0,0,0',
'2,1,0,0,1',
'5,1,0,1',
'4,1,0,2',
'3,1,0,4']

# priority_add(path_specification, target_node, path_priority)
# roll_poll(path_specification)
# print(path_specification)
# next_node, path_specification = node_select(path_specification, execute_node_l)
# next_node, path_specification = node_select(path_specification, execute_node_l)
# print(next_node)
num_poll = 0

# roll_poll(path_specification1)
# next_node, path_specification1, num_poll = node_select(path_specification1, execute_node_l1, num_poll)

roll_poll(path_specification5)
next_node, path_specification5, num_poll = node_select(path_specification5, execute_node_l5, num_poll)

pass
print(next_node)
# print(path_specification2)


