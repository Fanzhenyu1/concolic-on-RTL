import re

def node_dut():
    ## 打开display文件
    with open(flpath + flname_dut, 'r') as f:
        code = f.read()

    # # 使用正则表达式匹配所有节点编号
    pattern = r'"achieve node: ([\d,]+)"'
    nodes = re.findall(pattern, code)
    nodes = list(set(nodes))  # 去重
    # print(nodes)

    ## 计算节点数量
    node_all = len(nodes)
    # print("node_num:", node_all)
    return nodes, node_all

def node_sim():
    ## 打开log文件
    with open(flpath + flname_sim, 'r') as f:
        code = f.read()

    # # 使用正则表达式匹配所有节点编号
    pattern = r'achieve node: ([\d,]+)'
    nodes = re.findall(pattern, code)
    nodes = list(set(nodes))  # 去重
    # print(nodes)
    ## 计算节点数量
    node_get = len(nodes)
    # print("node_get:", node_get)
    return nodes, node_get

def main():
    node_miss_old = ['69,1,0,1', '60,1,0,1', '32,0,3,1,1', '60,1,0,0,1', '59,0,1,6', '59,0,1,5,0', '59,0,1,8', '59,0,1,6,1', '59,0,1,5', '59,0,1,5,1', '69,1,0,0,1', '59,0,1,6,0', '59,0,1,8,1', '59,0,1,4', '59,0,1,7,0', '64,1,0,0,1,1', '59,0,1,7', '59,0,1,7,1', '59,0,1,4,1', '59,0,1,6,0,1', '59,0,1,6,0,0', '67,1,1', '61,1,1', '63,1,0,0', '63,1,0,0,1']

    # 计算覆盖率
    l_nodes_all, node_all = node_dut()
    l_nodes_get, node_get = node_sim()
    coverage = node_get / node_all
    print("coverage:", coverage)

    # 输出节点覆盖情况
    print("node_all:", l_nodes_all)
    print("node_get:", l_nodes_get)
    node_miss = list(set(l_nodes_all) - set(l_nodes_get))
    print("node_miss:", node_miss)

    # 计算节点覆盖提升情况
    node_miss_new = list(set(node_miss_old).intersection(set(node_miss)))
    node_new_get = list(set(node_miss_old)-set(node_miss_new))
    print("node_new_get:", node_new_get)
    print("node_miss_new:", node_miss_new)
    print("new coverage:", (node_all - len(node_miss_new)) / node_all)
    return 0

if __name__ == '__main__':
    # 定义文件路径
    flpath = "D:/mylife_yanjiu/project/concolic_on_RTL/RTL/usb_phy/"
    flname_dut = "dut.v"
    flname_sim = "sim.log"
    main()
    