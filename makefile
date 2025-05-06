# 目标.v文件名
CASE := usb_phy

# 仿真参数
SEED := 8
NUM_CYCLES := 100

# 目标路径生成参数
DEEP := 3
TARGET_NODE :=  1,0,1
RESET := rst_i

# 工程根目录（根据实际情况修改）
RTL_DIR = /d/mylife_yanjiu/project/concolic_on_RTL/RTL

# 原始Verilog文件目录（如果需要在pre_process.py中用到，可在脚本内部处理）
SRC_DIR = $(RTL_DIR)/$(CASE)/src

# 预处理生成的Verilog文件
PRE_FILE = $(RTL_DIR)/$(CASE)/$(CASE)_1.v

# tb生成器输出的文件
TB_FILE = $(RTL_DIR)/$(CASE)/$(CASE)_tb.v

# CDFG生成的预处理文件
CDFG_FILE = $(RTL_DIR)/$(CASE)/$(CASE)_1_preprocessed.txt

# 插桩实现生成的dut文件
DUT_FILE = $(RTL_DIR)/$(CASE)/dut.v

# sim命令生成的仿真文件
VCD_FILE = $(RTL_DIR)/$(CASE)/wave.vcd
WAVE_FILE = $(RTL_DIR)/$(CASE)/wave
SIM_FILE = $(RTL_DIR)/$(CASE)/sim.log

.PHONY: sim path clean
# 默认目标：生成testbench
all: $(SRC_DIR) $(DUT_FILE)

# 创建目录
$(SRC_DIR):
	mkdir -p $(SRC_DIR)

# 运行pre_process.py，生成预处理后的Verilog文件
$(PRE_FILE): pre_process.py
	@echo "Generating $(CASE)_1.v ..."
	python3 pre_process.py $(CASE)
	@echo "generate $(CASE)_1.v finish."

verilog_format: $(PRE_FILE)
	@echo "Verilog_fromat continue..."
	verible-verilog-format --inplace "/d:/mylife_yanjiu/project/concolic_on_RTL/RTL/$(CASE)/$(CASE)_1.v"
	@echo "Verilog_fromat finish."

# 使用预处理后的文件运行tb_generator.py，生成testbench文件
tb: $(PRE_FILE) tb_generator.py
	@echo "Generating testbench..."
	python3 tb_generator.py $(CASE) $(NUM_CYCLES)
	@echo "generate $(CASE)_tb.v finish."

# 使用pre_process.py生成的文件后运行CDFG_1_1.py，并保存输出到CDFG_FILE
$(CDFG_FILE): verilog_format CDFG_1_1.py
	@echo "Generating CDFG..."
	python3 CDFG_1_1.py $(CASE)
	@echo "generate CDFG finish."

# 使用CDFG_display_1.py生成dut.v
$(DUT_FILE): $(CDFG_FILE) CDFG_display_1.py
	@echo "Generating dut.v..."
	python3 CDFG_display_1.py $(CASE)
	@echo "generate dut.v finish."

# 独立的 simulation 目标，执行 simulation.py
sim: simulation.py
	python3 simulation.py $(CASE) $(SEED)
	@echo "Simulation finish."
	@echo "Starting coverage analysis..."
	python3 coverage.py $(CASE)
	@echo "Coverage analysis finish."

z3def: z3_signal_define.py
	python3 z3_signal_define.py $(CASE)
	@echo "Generate z3 signal define finish."

path: target_path_1_1.py
	python3 target_path_1_1.py $(DEEP) $(TARGET_NODE) $(RESET)
	@echo "Generate target path finish."

# 清理生成的文件
clean:
	rm -f $(PRE_FILE) $(TB_FILE) $(CDFG_FILE) $(DUT_FILE) $(VCD_FILE) $(WAVE_FILE) $(SIM_FILE)
