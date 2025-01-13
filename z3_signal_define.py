signal_inout = {'in': 8, 'clk': 1, 'rst': 1, 'out': 8, 'state': 4, 'st': 4, 'st2': 4}
# 自动生成 Z3Py 定义的代码字符串
z3_code = ""
for signal_name, bit_width in signal_inout.items():
    z3_code += f"{signal_name} = BitVec('{signal_name}', {bit_width})\n"

print("自动生成的 Z3Py 代码：\n")
print(z3_code)
