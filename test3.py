def period_unify(path_list, now_node):    # 路径时序约束统一化
    # 添加初始优先级参数
    global num_start
    up_node = []    # 上级可能节点，列表
    up_node_time = []    # 上级可能节点的时序参数列表
    flag_error = 0
    for i in range(len(path_list)):
        if path_list[i][0] == now_node:
            path_list[i].append(num_start)
            up_node.append(path_list[i][1])
            up_node_time.append(int(path_list[i][3]))
            flag_error += 1
            pass
        else:
            continue
    if flag_error == 0:
        return 0
    for i in range(len(up_node)):
        for j in range(len(path_list)):
            if path_list[j][0] == up_node[i]:
                if up_node_time[i] + int(path_list[j][3]) <= 1:
                    path_list[j][0] = now_node
                pass
    pass
    num_start += 1
    return 0

path_list = [['1,0,3,0,0', '0,1',       '1', '0'], 
             ['0,1',       '1,0,2,0,1', '0', '1'], 
             ['0,1',       '1,0,3,1',   '0', '1'], 
             ['0,1',       '1,0,3,0,0', '0', '1']]
now_node = '1,0,3,0,0'
num_start = 1
period_unify(path_list, now_node)