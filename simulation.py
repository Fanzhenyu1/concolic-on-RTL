import subprocess
import os
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
def main_process():
    commands = [
        # "cd d:/mylife_yanjiu/project/concolic_on_RTL/RTL/core/clint/",  # 打开路径
        "iverilog -o wave clint.v clint_tb.v",  # 第一条命令
        "vvp -n wave lxt2"                         # 第二条命令（假设需仿真）
        # ,"gtkwave wave.vcd"                         # 第三条命令（假设需查看波形）
    ]

    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"执行成功：{cmd}")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"执行失败：{cmd}")
            print(f"错误信息：{e.stderr}")
            break  # 出现错误时终止后续命令
    else:
        print("所有命令执行完毕！")
    return 0

def main():
    # 加强版垃圾回收
    for _ in range(3):
        gc.collect()
    monitor = MemoryMonitor()
    monitor.start()
    monitor.ready_event.wait()
    start_time = time.time()
    
    main_process()

    end_time = time.time()
    monitor.stop()
    gc.collect()
    print(f"程序运行时间：{end_time - start_time}s")
    print(f"最大内存使用量：{monitor.peak_memory:.2f}KB")
    return 0

if __name__ == '__main__':
    main()
