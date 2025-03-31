# Makefile for Verilog processing pipeline

# 用户可配置参数
MODULE      := case1
BASE_DIR    := /d/mylife_yanjiu/project/concolic_on_RTL/
SRC_DIR     := $(BASE_DIR)/RTL/$(MODULE)/src/
OUT_DIR     := $(BASE_DIR)/RTL/$(MODULE)/

# 文件路径定义
ORIGINAL    := $(SRC_DIR)/$(MODULE).v
PRE_PROC    := $(OUT_DIR)/$(MODULE)_1.v
TB_GEN      := $(OUT_DIR)/$(MODULE)_tb.v

# 工具命令
PYTHON      := python3
MKDIR       := mkdir -p

.PHONY: all clean help





clean:
	@echo "cleaning..."
	@if [ -d "$(OUT_DIR)" ]; then \
		echo "Removing wave files..."; \
		rm -rf "$(OUT_DIR)/wave"; \
		echo "Deleting target files (excluding 'src/*.v')..."; \
		find "$(OUT_DIR)" \
			-type f \( -name '*.txt' -o -name '*.log' -o -name '*.vcd' \) -delete; \
		find "$(OUT_DIR)" \
			-type f -name '*.v' -not -path "$(OUT_DIR)/src/*/*.v" -delete; \
		echo "Cleaning empty directories (except 'src')..."; \
		find "$(OUT_DIR)" -type d -empty -not -path "$(OUT_DIR)/src" -not -path "$(OUT_DIR)/src/*" -delete; \
		echo "clean finish!"; \
	else \
		echo "$(OUT_DIR) not exist, nothing to clean!"; \
	fi


help: ## 显示帮助信息
	@echo "可用命令:"
	@echo "  make [MODULE=name]   - 处理指定模块 (默认: case1)"
	@echo "  make clean          - 清理生成文件"
	@echo "  make help           - 显示此帮助"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
