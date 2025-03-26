from math import *
import re
from z3 import *
import verilog2z3
import time
import psutil
import gc
from threading import Thread, Event

class MemoryMonitor(Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = Event()
        self.peak_memory = 0  # 单位：KB
        self.process = psutil.Process(os.getpid())
        self.ready_event = Event()  # 新增准备就绪信号

    def _get_current_memory(self):
        """获取当前进程内存使用量"""
        return self.process.memory_info().rss / 1024  # 转换为KB

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

def not_empty(s):
    return s and s.strip()

def main(constraints):

    # 加强版垃圾回收
    for _ in range(3):
        gc.collect()
    monitor = MemoryMonitor()
    monitor.start()
    monitor.ready_event.wait()

    start_time = time.time()

    ## 主体功能body begin
    solver = Solver()
    signal_list, constraints = verilog2z3.verilog_to_z3(constraints,[],[])
    print(f"约束列表：{constraints}")
    pass
    for constraint in constraints:
        solver.add(eval(constraint))    
    if solver.check() == sat:
        print(f"当前路径约束下有解")
        model = solver.model()
        print(f"解为：{model}")
    else:
        print(f"当前路径约束下无解")
    ## 主体功能body end

    monitor.stop()
    # monitor.join()
    end_time = time.time()
    execution_time = end_time - start_time
    gc.collect()
    print("Execution time in seconds: ", execution_time)
    print(f"峰值内存占用：{monitor.peak_memory:.2f} KB")
    return 0

if __name__ == '__main__':

    ## define BitVec variables

    ## usb_phy.v
    # rst = BitVec('rst', 1)
    # phy_tx_mode = BitVec('phy_tx_mode', 1)
    # usb_rst = BitVec('usb_rst', 1)
    # txdp = BitVec('txdp', 1)
    # txdn = BitVec('txdn', 1)
    # txoe = BitVec('txoe', 1)
    # rxd = BitVec('rxd', 1)
    # rxdp = BitVec('rxdp', 1)
    # rxdn = BitVec('rxdn', 1)
    # DataOut_i = BitVec('DataOut_i', 8)
    # TxValid_i = BitVec('TxValid_i', 1)
    # TxReady_o = BitVec('TxReady_o', 1)
    # RxValid_o = BitVec('RxValid_o', 1)
    # RxActive_o = BitVec('RxActive_o', 1)
    # RxError_o = BitVec('RxError_o', 1)
    # DataIn_o = BitVec('DataIn_o', 8)
    # LineState_o = BitVec('LineState_o', 2)
    # rst_cnt = BitVec('rst_cnt', 5)
    # i_tx_phy_TxReady_o = BitVec('i_tx_phy_TxReady_o', 1)
    # i_tx_phy_state = BitVec('i_tx_phy_state', 3)
    # i_tx_phy_next_state = BitVec('i_tx_phy_next_state', 3)
    # i_tx_phy_tx_ready_d = BitVec('i_tx_phy_tx_ready_d', 1)
    # i_tx_phy_ld_sop_d = BitVec('i_tx_phy_ld_sop_d', 1)
    # i_tx_phy_ld_data_d = BitVec('i_tx_phy_ld_data_d', 1)
    # i_tx_phy_ld_eop_d = BitVec('i_tx_phy_ld_eop_d', 1)
    # i_tx_phy_tx_ip = BitVec('i_tx_phy_tx_ip', 1)
    # i_tx_phy_tx_ip_sync = BitVec('i_tx_phy_tx_ip_sync', 1)
    # i_tx_phy_bit_cnt = BitVec('i_tx_phy_bit_cnt', 3)
    # i_tx_phy_hold_reg = BitVec('i_tx_phy_hold_reg', 8)
    # i_tx_phy_hold_reg_d = BitVec('i_tx_phy_hold_reg_d', 8)
    # i_tx_phy_sd_raw_o = BitVec('i_tx_phy_sd_raw_o', 1)
    # i_tx_phy_data_done = BitVec('i_tx_phy_data_done', 1)
    # i_tx_phy_sft_done = BitVec('i_tx_phy_sft_done', 1)
    # i_tx_phy_sft_done_r = BitVec('i_tx_phy_sft_done_r', 1)
    # i_tx_phy_ld_data = BitVec('i_tx_phy_ld_data', 1)
    # i_tx_phy_one_cnt = BitVec('i_tx_phy_one_cnt', 3)
    # i_tx_phy_stuff = BitVec('i_tx_phy_stuff', 1)
    # i_tx_phy_sd_bs_o = BitVec('i_tx_phy_sd_bs_o', 1)
    # i_tx_phy_sd_nrzi_o = BitVec('i_tx_phy_sd_nrzi_o', 1)
    # i_tx_phy_append_eop = BitVec('i_tx_phy_append_eop', 1)
    # i_tx_phy_append_eop_sync1 = BitVec('i_tx_phy_append_eop_sync1', 1)
    # i_tx_phy_append_eop_sync2 = BitVec('i_tx_phy_append_eop_sync2', 1)
    # i_tx_phy_append_eop_sync3 = BitVec('i_tx_phy_append_eop_sync3', 1)
    # i_tx_phy_append_eop_sync4 = BitVec('i_tx_phy_append_eop_sync4', 1)
    # i_tx_phy_txdp = BitVec('i_tx_phy_txdp', 1)
    # i_tx_phy_txdn = BitVec('i_tx_phy_txdn', 1)
    # i_tx_phy_txoe_r1 = BitVec('i_tx_phy_txoe_r1', 1)
    # i_tx_phy_txoe_r2 = BitVec('i_tx_phy_txoe_r2', 1)
    # i_tx_phy_txoe = BitVec('i_tx_phy_txoe', 1)
    # i_rx_phy_rxd_s0 = BitVec('i_rx_phy_rxd_s0', 1)
    # i_rx_phy_rxd_s1 = BitVec('i_rx_phy_rxd_s1', 1)
    # i_rx_phy_rxd_s = BitVec('i_rx_phy_rxd_s', 1)
    # i_rx_phy_rxdp_s0 = BitVec('i_rx_phy_rxdp_s0', 1)
    # i_rx_phy_rxdp_s1 = BitVec('i_rx_phy_rxdp_s1', 1)
    # i_rx_phy_rxdp_s = BitVec('i_rx_phy_rxdp_s', 1)
    # i_rx_phy_rxdp_s_r = BitVec('i_rx_phy_rxdp_s_r', 1)
    # i_rx_phy_rxdn_s0 = BitVec('i_rx_phy_rxdn_s0', 1)
    # i_rx_phy_rxdn_s1 = BitVec('i_rx_phy_rxdn_s1', 1)
    # i_rx_phy_rxdn_s = BitVec('i_rx_phy_rxdn_s', 1)
    # i_rx_phy_rxdn_s_r = BitVec('i_rx_phy_rxdn_s_r', 1)
    # i_rx_phy_synced_d = BitVec('i_rx_phy_synced_d', 1)
    # i_rx_phy_rxd_r = BitVec('i_rx_phy_rxd_r', 1)
    # i_rx_phy_rx_en = BitVec('i_rx_phy_rx_en', 1)
    # i_rx_phy_rx_active = BitVec('i_rx_phy_rx_active', 1)
    # i_rx_phy_bit_cnt = BitVec('i_rx_phy_bit_cnt', 3)
    # i_rx_phy_rx_valid1 = BitVec('i_rx_phy_rx_valid1', 1)
    # i_rx_phy_rx_valid = BitVec('i_rx_phy_rx_valid', 1)
    # i_rx_phy_shift_en = BitVec('i_rx_phy_shift_en', 1)
    # i_rx_phy_sd_r = BitVec('i_rx_phy_sd_r', 1)
    # i_rx_phy_sd_nrzi = BitVec('i_rx_phy_sd_nrzi', 1)
    # i_rx_phy_hold_reg = BitVec('i_rx_phy_hold_reg', 8)
    # i_rx_phy_one_cnt = BitVec('i_rx_phy_one_cnt', 3)
    # i_rx_phy_dpll_state = BitVec('i_rx_phy_dpll_state', 2)
    # i_rx_phy_dpll_next_state = BitVec('i_rx_phy_dpll_next_state', 2)
    # i_rx_phy_fs_ce_d = BitVec('i_rx_phy_fs_ce_d', 1)
    # i_rx_phy_fs_ce = BitVec('i_rx_phy_fs_ce', 1)
    # i_rx_phy_fs_state = BitVec('i_rx_phy_fs_state', 3)
    # i_rx_phy_fs_next_state = BitVec('i_rx_phy_fs_next_state', 3)
    # i_rx_phy_rx_valid_r = BitVec('i_rx_phy_rx_valid_r', 1)
    # i_rx_phy_sync_err_d = BitVec('i_rx_phy_sync_err_d', 1)
    # i_rx_phy_sync_err = BitVec('i_rx_phy_sync_err', 1)
    # i_rx_phy_bit_stuff_err = BitVec('i_rx_phy_bit_stuff_err', 1)
    # i_rx_phy_se0_r = BitVec('i_rx_phy_se0_r', 1)
    # i_rx_phy_byte_err = BitVec('i_rx_phy_byte_err', 1)
    # i_rx_phy_se0_s = BitVec('i_rx_phy_se0_s', 1)
    # i_rx_phy_fs_ce_r1 = BitVec('i_rx_phy_fs_ce_r1', 1)
    # i_rx_phy_fs_ce_r2 = BitVec('i_rx_phy_fs_ce_r2', 1)

    ## case3.v
    rst = BitVec('rst', 1)
    input_a = BitVec('input_a', 32)
    input_b = BitVec('input_b', 32)
    ctr = BitVec('ctr', 32)
    ctr_1 = BitVec('ctr', 32)
    ctr_2 = BitVec('ctr', 32)
    ht_out = BitVec('ht_out', 32)
    signal1 = BitVec('signal1', 1)
    signal2 = BitVec('signal1', 1)
    signal3 = BitVec('signal1', 1)
    trigger = BitVec('trigger', 1)

    constraints = ["input_b == 32'h55667788 && signal1", "trigger = signal1 & signal2 & signal3;", "ctr_2 <= ctr_1;", "signal3 <= 1'b1;"]

    main(constraints)

