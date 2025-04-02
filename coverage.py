import re
import argparse

def node_dut(flpath, flname_dut):
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

def node_sim(flpath, flname_sim):
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

def main(module_name):
    # 定义文件路径
    flpath = f"D:/mylife_yanjiu/project/concolic_on_RTL/RTL/{module_name}/"
    flname_dut = "dut.v"
    flname_sim = "sim.log"

    node_miss_old = ['59,0,1,6,0', '59,0,1,6,0,0', '30,1,0,1', '69,1,0,0,1', '17,1,0,0,1', '54,0,4', '67,1,1', '12,1,0,5', '8,1,0,0,1', '60,1,0,0,1', '12,1,0,2', '63,1,0,0,1', '59,0,1,6,1', '64,1,0,1', '68,1,0,1', '21,1,0,0,1', '0,1,0,0,1', '59,0,1,6', '25,1,0,1', '12,1,0,8', '54,0,1,1', '32,0,6', '12,1,0,7', '59,0,1,7,1', '10,1,0,1', '59,0,1,2', '59,0,1,2,0', '59,0,1,3', '69,1,0,1', '59,0,1,4,0', '64,1,0,0,1,0', '59,0,1,8,1', '32,0,3,1', '9,1,0,1', '17,1,0,0,1,0', '59,0,1,3,0', '20,1,0,0,1', '32,0,3,1,1', '12,1,0,3', '64,1,0,0,1', '60,1,0,1', '26,1,0,1', '15,1,0,1', '24,1,0,1', '28,1,0,1', '54,0,3,0', '61,1,1', '32,0,4', '59,0,1,3,1', '27,1,0,1', '59,0,1,8', '32,0,3', '22,1,0,1', '0,1,0,1', '19,1,0,1', '21,1,0,1', '8,1,0,1', '59,0,1,5,1', '54,0,3', '17,1,0,1', '59,0,1,7', '59,0,1,6,0,1', '29,1,0,1', '63,1,0,1', '59,0,1,4,1', '11,1,0,0,1', '20,1,0,1', '54,0,3,1', '32,0,2', '23,1,0,1', '54,0,4,1', '59,0,1,4', '32,0,2,1', '59,0,1,2,1', '54,0,4,0', '32,0,5', '32,0,6,1', '11,1,0,1', '12,1,0,6', '59,0,1,7,0', '12,1,0,1', '17,1,0,0,1,1', '54,0,1,0', '59,0,1,5', '59,0,1,5,0', '64,1,0,0,1,1', '12,1,0,4', '54,0,1', '68,1,0,0,1']

    # 计算覆盖率
    l_nodes_all, node_all = node_dut(flpath, flname_dut)
    l_nodes_get, node_get = node_sim(flpath, flname_sim)
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
    