import time
import psutil
import os
import gc
from threading import Thread, Event

class MemoryMonitor(Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = Event()
        self.peak_memory = 0  # 单位：MB
        self.process = psutil.Process(os.getpid())
        self.ready_event = Event()  # 新增准备就绪信号

    def _get_current_memory(self):
        """获取当前进程内存使用量"""
        return self.process.memory_info().rss / (1024 * 1024)  # 转换为MB

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

def monitored_task():
    """需要监控的程序代码"""
    # 更明显的内存分配测试
    data = []
    for _ in range(5):
        data.append(bytearray(8 * 1024 * 1024))  # 每次分配8MB
        time.sleep(0.01)
    return len(data)

def profile_execution():
    """执行内存和耗时分析"""
    # 加强版垃圾回收
    for _ in range(3):
        gc.collect()
    
    # 创建并启动监控线程
    monitor = MemoryMonitor()
    monitor.start()
    
    # 等待监控线程初始化完成
    monitor.ready_event.wait()
    
    # 记录高精度开始时间
    start_time = time.perf_counter()
    
    # 执行目标程序
    result = monitored_task()
    
    # 停止监控
    monitor.stop()
    
    # 计算总运行时间
    execution_time = time.perf_counter() - start_time

    # 输出结果
    print(f"✅ 任务返回值: {result}")
    print(f"🕒 程序运行时长：{execution_time*1000:.2f}毫秒")
    print(f"📈 净内存占用峰值：{monitor.peak_memory:.2f} MB")
    print("─" * 40)

if __name__ == "__main__":
    # 多次执行测试
    for i in range(3):
        print(f"第 {i+1} 次执行结果：")
        profile_execution()
        time.sleep(1)  # 增加执行间隔