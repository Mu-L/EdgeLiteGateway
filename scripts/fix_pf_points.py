#!/usr/bin/env python3
"""在 ProtoForge 中为 6 个缺失点位的设备重新创建带点位的配置。"""
import json
import time
import urllib.request
import urllib.error

PF = "http://127.0.0.1:8000/api/v1"

def pf_login():
    data = json.dumps({"username": "admin", "password": "admin", "no_revoke": True}).encode()
    req = urllib.request.Request(f"{PF}/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.load(resp)
    payload = body.get("data") if isinstance(body.get("data"), dict) else body
    return payload["access_token"]

def pf_api(token, method, path, body=None):
    req = urllib.request.Request(f"{PF}{path}", method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:500]}

token = pf_login()

# 设备配置（与 EdgeLite 侧点位名和地址保持一致）
DEVICES = {
    "pf-modbus": {
        "id": "pf-modbus",
        "name": "PF Modbus TCP",
        "protocol": "modbus_tcp",
        "protocol_config": {"port": 5020},
        "points": [
            {"name": "temp", "address": "HR100", "data_type": "float32", "access": "rw", "fixed_value": 66.6},
            {"name": "word1", "address": "HR102", "data_type": "int16", "access": "rw", "fixed_value": 4321},
            {"name": "coil1", "address": "C0", "data_type": "bool", "access": "rw", "fixed_value": True},
            {"name": "coil2", "address": "C1", "data_type": "bool", "access": "rw", "fixed_value": False},
            {"name": "di1", "address": "I0", "data_type": "bool", "access": "r", "fixed_value": True},
            {"name": "speed", "address": "HR104", "data_type": "int16", "access": "rw", "fixed_value": 888},
        ],
    },
    "pf-s7": {
        "id": "pf-s7",
        "name": "PF Siemens S7",
        "protocol": "s7",
        "protocol_config": {"port": 102},
        "points": [
            {"name": "temp", "address": "DB1.D0", "data_type": "float32", "access": "rw", "fixed_value": 12.5},
            {"name": "word1", "address": "DB1.W4", "data_type": "int16", "access": "rw", "fixed_value": 1000},
            {"name": "bit1", "address": "DB1.X6.0", "data_type": "bool", "access": "rw", "fixed_value": True},
            {"name": "bit2", "address": "M10.0", "data_type": "bool", "access": "rw", "fixed_value": False},
        ],
    },
    "pf-mc": {
        "id": "pf-mc",
        "name": "PF Mitsubishi MC",
        "protocol": "mc",
        "protocol_config": {"port": 5000},
        "points": [
            {"name": "d0", "address": "D0", "data_type": "int16", "access": "rw", "fixed_value": 555},
        ],
    },
    "pf-fins": {
        "id": "pf-fins",
        "name": "PF Omron FINS",
        "protocol": "fins",
        "protocol_config": {"port": 9600},
        "points": [
            {"name": "w0", "address": "D0", "data_type": "uint16", "access": "rw", "fixed_value": 1234},
            {"name": "f2", "address": "D2", "data_type": "float32", "access": "rw", "fixed_value": 0.0},
            {"name": "w10", "address": "D10", "data_type": "uint16", "access": "rw", "fixed_value": 0},
            {"name": "b20", "address": "D20.0", "data_type": "bool", "access": "rw", "fixed_value": False},
        ],
    },
    "pf-ab": {
        "id": "pf-ab",
        "name": "PF Allen-Bradley",
        "protocol": "ab",
        "protocol_config": {"port": 44818},
        "points": [
            {"name": "Temperature", "address": "Temperature", "data_type": "float32", "access": "rw", "fixed_value": 26.5},
            {"name": "Setpoint", "address": "Setpoint", "data_type": "float32", "access": "rw", "fixed_value": 50},
        ],
    },
    "pf-mqtt": {
        "id": "pf-mqtt",
        "name": "PF MQTT",
        "protocol": "mqtt",
        "protocol_config": {"broker": "127.0.0.1", "port": 1883, "topic_prefix": "protoforge"},
        "points": [
            {"name": "temp", "address": "pf-mqtt/temp", "data_type": "float32", "access": "rw", "fixed_value": 36.6},
            {"name": "switch", "address": "pf-mqtt/switch", "data_type": "float32", "access": "rw", "fixed_value": 0.0},
        ],
    },
}

# 删除并重新创建设备
for dev_id, config in DEVICES.items():
    print(f"=== 重建 {dev_id} ===")
    # 先删除
    code, data = pf_api(token, "DELETE", f"/devices/{dev_id}")
    print(f"  删除: HTTP {code}")
    time.sleep(1)
    # 重新创建
    code, data = pf_api(token, "POST", "/devices", config)
    if code == 200:
        print(f"  创建: HTTP {code} OK")
    else:
        print(f"  创建: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:300] if data else ''}")
    time.sleep(1)

# 等待设备启动
print("\n等待设备启动 (10s)...")
time.sleep(10)

# 写入特征值
print("\n=== 写入特征值 ===")
WRITE_SPECS = [
    ("pf-modbus", "temp", 66.6), ("pf-modbus", "word1", 4321),
    ("pf-s7", "temp", 12.5), ("pf-s7", "word1", 1000),
    ("pf-mc", "d0", 555),
    ("pf-fins", "w0", 1234),
    ("pf-ab", "Temperature", 26.5),
    ("pf-mqtt", "temp", 36.6),
]
for dev_id, point, value in WRITE_SPECS:
    code, data = pf_api(token, "PUT", f"/devices/{dev_id}/points/{point}", {"value": value})
    print(f"  {dev_id}/{point}={value}: HTTP {code}")

# 验证
print("\n=== 验证 ProtoForge 设备点位 ===")
for dev_id in DEVICES:
    code, data = pf_api(token, "GET", f"/devices/{dev_id}")
    if code == 200:
        d = data.get("device", data) if isinstance(data, dict) else data
        points = d.get("points", [])
        pts = {p.get("name"): p.get("value") for p in points}
        print(f"  {dev_id}: {pts}")
    else:
        print(f"  {dev_id}: HTTP {code}")
