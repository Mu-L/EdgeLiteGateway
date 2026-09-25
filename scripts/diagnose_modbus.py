#!/usr/bin/env python3
"""用 Modbus 客户端直接读取 ProtoForge Modbus 服务器的寄存器值。"""
from pymodbus.client import ModbusTcpClient

cli = ModbusTcpClient("127.0.0.1", port=5020)
try:
    cli.connect()
    # 尝试不同的 slave_id
    for slave_id in [1, 5]:
        print(f"\n=== Slave ID: {slave_id} ===")
        # 读 holding registers 98-110
        rr = cli.read_holding_registers(address=98, count=15, device_id=slave_id)
        if not rr.isError():
            print(f"  HR[98-112]: {rr.registers}")
        else:
            print(f"  HR[98-112]: Error: {rr}")
        
        # 读 holding registers 0-10
        rr = cli.read_holding_registers(address=0, count=12, device_id=slave_id)
        if not rr.isError():
            print(f"  HR[0-11]: {rr.registers}")
        else:
            print(f"  HR[0-11]: Error: {rr}")
        
        # 读 coils 0-5
        rr = cli.read_coils(address=0, count=6, device_id=slave_id)
        if not rr.isError():
            print(f"  C[0-5]: {rr.bits}")
        else:
            print(f"  C[0-5]: Error: {rr}")
        
        # 读 discrete inputs 0-5
        rr = cli.read_discrete_inputs(address=0, count=6, device_id=slave_id)
        if not rr.isError():
            print(f"  DI[0-5]: {rr.bits}")
        else:
            print(f"  DI[0-5]: Error: {rr}")
finally:
    cli.close()

# 现在检查 ProtoForge pf-modbus 的 slave_id
# 从 diagnose_pf2.py 看到 protocol_config 有 slave_id=5
# 但 EdgeLite pf-modbus 的 config 中 slave_id=1
# 这可能是地址映射不匹配的原因

print("\n=== 结论 ===")
print("ProtoForge pf-modbus 的 slave_id=5（在 protocol_config 中）")
print("EdgeLite pf-modbus 的 slave_id=1（在 config 中）")
print("需要将 EdgeLite 的 slave_id 改为 5，或者将 ProtoForge 的 slave_id 改为 1")
