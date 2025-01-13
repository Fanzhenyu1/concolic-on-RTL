import re

# Verilog 表达式
verilog_expr = "assign result = (a & b) | ( 2'b0 ^ 'h0F) & ~e;"
str1 = "r_in == 6'b0 || (r_in == 6'b111111 && r_in == 6'b101010)"
# 正则表达式模式
signal_pattern = r'(?<!\')\b[a-zA-Z_]\w*\b'  # 匹配信号，但排除以单引号开头的数字常量
constant_pattern = r"[0-9]?[0-9]?'\w[0-9A-Fa-f_]+'?"    # 匹配 Verilog 数字常量
operator_pattern = r'[&|^~!=()]+'                # 匹配操作符

# 提取信号
signals = re.findall(signal_pattern, str1)

# 提取数字常量
constants = re.findall(constant_pattern, str1)

# 提取操作符
operators = re.findall(operator_pattern, str1)

# 去重信号（可能包含关键词，如assign，需要过滤）
verilog_keywords = {"assign"}
signals = [s for s in signals if s not in verilog_keywords]

print("提取的信号:", signals)
print("提取的数字常量:", constants)
print("提取的操作符:", operators)
