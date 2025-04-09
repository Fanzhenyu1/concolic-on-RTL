import subprocess
import os
import random
import argparse
import time
import psutil
import gc
from threading import Thread, Event


# 监控模块
class MemoryMonitor(Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = Event()
        self.peak_memory = 0  # 单位：MB
        self.process = psutil.Process(os.getpid())
        self.ready_event = Event()  # 新增准备就绪信号

    def _get_current_memory(self):
        total = self.process.memory_info().rss
        for child in self.process.children(recursive=True):  # 递归统计子进程
            total += child.memory_info().rss
        return total / 1024  # KB

    def run(self):
        """持续监控内存使用情况"""
        # 在监控开始时获取初始内存
        initial_memory = self._get_current_memory()
        self.ready_event.set()  # 发出准备就绪信号
        
        while not self.stop_event.wait(timeout=0.001):  # 采样间隔提升到1ms
            current_mem = self._get_current_memory() - initial_memory
            if current_mem > self.peak_memory:
                self.peak_memory = current_mem

    def stop(self):
        """停止监控线程"""
        self.stop_event.set()
        self.join(timeout=1)

# 主进程
def main_process(module_name, seed_value=0):

    fl_path = f"d:/mylife_yanjiu/project/concolic_on_RTL/RTL/{module_name}/"
    # seed_value = random.randint(0, 4294967295)
    commands = [
        # "cd d:/mylife_yanjiu/project/concolic_on_RTL/RTL/case1/",  # 打开路径
        f"iverilog -g2012 -o {fl_path}wave {fl_path}dut.v {fl_path}{module_name}_tb.v",  # 第一条命令
        f"vvp -n {fl_path}wave +SEED={seed_value} lxt2 > {fl_path}sim.log"                         # 第二条命令（假设需仿真）
        # ,f"gtkwave {fl_path}wave.vcd"                         # 第三条命令（假设需查看波形）
    ]

    for cmd in commands:
        try:
            result = subprocess.run(cmd, cwd=fl_path, shell=True, check=True, capture_output=True, text=True)
            print(f"执行成功：{cmd}")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"执行失败：{cmd}")
            print(f"错误信息：{e.stderr}")
            break  # 出现错误时终止后续命令
    else:
        print("所有命令执行完毕！")
    return 0

def main(module_name, seed_value):

    for _ in range(3):  # 重复执行3次
        gc.collect()
    monitor = MemoryMonitor()
    monitor.start()
    monitor.ready_event.wait()
    start_time = time.time()
    
    main_process(module_name, seed_value)

    end_time = time.time()
    monitor.stop()
    gc.collect()
    print(f"程序运行时间：{end_time - start_time}s")
    print(f"最大内存使用量：{monitor.peak_memory:.2f}KB")
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
    parser.add_argument("seed", 
                      type=int,
                      help="Value of the random seed")    
    
    # 可选参数示例
    parser.add_argument("-o", "--output",
                      default="_1_preprocessed.txt",
                      help="Output file suffix")
    
    # 解析参数
    args = parser.parse_args()

    main(module_name=args.module, seed_value=args.seed)
