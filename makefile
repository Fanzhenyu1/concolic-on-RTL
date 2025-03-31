# 可调参数，默认case1
CASE ?= case1

# 工程根目录（根据实际情况修改）
RTL_DIR = /d/mylife_yanjiu/project/concolic_on_RTL/RTL

# 原始Verilog文件目录（如果需要在pre_process.py中用到，可在脚本内部处理）
SRC_DIR = $(RTL_DIR)/$(CASE)/src

# 预处理生成的Verilog文件
PRE_FILE = $(RTL_DIR)/$(CASE)/$(CASE)_1.v

# tb生成器输出的文件
TB_FILE = $(RTL_DIR)/$(CASE)/case1_tb.v

CDFG_FILE = $(RTL_DIR)/$(CASE)/cdfg.txt

# 默认目标：生成testbench
all: $(TB_FILE) $(CDFG_FILE)

# 运行pre_process.py，生成预处理后的Verilog文件
$(PRE_FILE): pre_process.py
	python pre_process.py $(CASE)

# 使用预处理后的文件运行tb_generator.py，生成testbench文件
$(TB_FILE): $(PRE_FILE) tb_generator.py
	python tb_generator.py

# 使用pre_process.py生成的文件后运行CDFG_1_1.py，并保存输出到CDFG_FILE
$(CDFG_FILE): $(PRE_FILE) CDFG_1_1.py
	python CDFG_1_1.py $(CASE) > $(CDFG_FILE)

# 清理生成的文件
clean:
	rm -f $(PRE_FILE) $(TB_FILE) $(CDFG_FILE)
