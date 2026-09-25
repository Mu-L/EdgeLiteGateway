#!/usr/bin/env python3
"""综合修复脚本：
1. 在 ProtoForge 创建 pf-mc, pf-http 设备
2. 修复 pf-opcua 点名 (添加 motor_speed/valve_open)
3. 修复 pf-fins 地址映射 (w0 应映射到 W0 而非 D0)
4. 修复 pf-mqtt 订阅 topic
5. 启动 ProtoForge AB 协议
6. 在 EdgeLite 创建缺失的 pf-mc, pf-opcua, pf-http 设备
"""
import json
import time
import urllib.request
import urllib.error

PF = "http://127.0.0.1:8000/api/v1"
EL = "http://127.0.0.1:8180/api/v1"
PF_USER = "admin"
PF_PASS = "admin"
EL_USER = "admin"
EL_PASS = "EdgeLite@2026"


def login(base, user, password, token_field="access_token"):
    data = json.dumps({"username": user, "password": password}).encode()
    req = urllib.request.Request(f"{base}/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.load(resp)
    payload = body.get("data") if isinstance(body.get("data"), dict) else body
    return payload[token_field]


def api(base, token, method, path, body=None):
    req = urllib.request.Request(f"{base}{path}", method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=20) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:500]}


pf_token = login(PF, PF_USER, PF_PASS)
el_token = login(EL, EL_USER, EL_PASS)

# ===================================================================
# 1. 在 ProtoForge 创建 pf-mc 设备
# ===================================================================
print("=== 1. 创建 ProtoForge pf-mc 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices/pf-mc")
if code == 404:
    # 创建 MC 设备
    mc_device = {
        "id": "pf-mc",
        "name": "PF Mitsubishi MC",
        "protocol": "mc",
        "points": [
            {"name": "d0", "data_type": "int16", "address": "D0"},
        ],
    }
    code, data = api(PF, pf_token, "POST", "/devices", mc_device)
    print(f"  创建 pf-mc: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"  pf-mc 已存在: HTTP {code}")

# 写入特征值
code, data = api(PF, pf_token, "PUT", "/devices/pf-mc/points/d0", {"value": 555})
print(f"  写入 d0=555: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")

# ===================================================================
# 2. 在 ProtoForge 创建 pf-http 设备
# ===================================================================
print("\n=== 2. 创建 ProtoForge pf-http 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices/pf-http")
if code == 404:
    http_device = {
        "id": "pf-http",
        "name": "PF HTTP Webhook",
        "protocol": "http",
        "points": [
            {"name": "temperature", "data_type": "float32", "address": "temperature"},
            {"name": "pressure", "data_type": "float32", "address": "pressure"},
        ],
    }
    code, data = api(PF, pf_token, "POST", "/devices", http_device)
    print(f"  创建 pf-http: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"  pf-http 已存在: HTTP {code}")

# 写入特征值
for name, val in [("temperature", 42.0), ("pressure", 1.5)]:
    code, data = api(PF, pf_token, "PUT", f"/devices/pf-http/points/{name}", {"value": val})
    print(f"  写入 {name}={val}: HTTP {code}")

# ===================================================================
# 3. 修复 pf-opcua: 添加 motor_speed/valve_open 点位
# ===================================================================
print("\n=== 3. 修复 ProtoForge pf-opcua 点位 ===")
# 先检查现有点位
code, data = api(PF, pf_token, "GET", "/devices/pf-opcua/points")
if code == 200 and data:
    existing = {p["name"] for p in data.get("points", [])}
    print(f"  现有点位: {existing}")
    # 添加缺失的 motor_speed 和 valve_open
    for name, dtype, val in [("motor_speed", "int32", 1500), ("valve_open", "bool", True)]:
        if name not in existing:
            code2, data2 = api(PF, pf_token, "POST", "/devices/pf-opcua/points",
                               {"name": name, "data_type": dtype, "address": f"ns=2;s={name}"})
            print(f"  添加 {name}: HTTP {code2}: {json.dumps(data2, ensure_ascii=False)[:200]}")
        # 写入特征值
        code3, data3 = api(PF, pf_token, "PUT", f"/devices/pf-opcua/points/{name}", {"value": val})
        print(f"  写入 {name}={val}: HTTP {code3}")

# ===================================================================
# 4. 修复 pf-fins: w0 地址应为 W0 而非 D0
# ===================================================================
print("\n=== 4. 检查 pf-fins 地址映射 ===")
# ProtoForge 端 w0 写入成功(=1234)，但 EdgeLite 读到 0
# EdgeLite 地址是 D0,w (DM区字地址)，但 ProtoForge 设备点名 w0
# 问题可能是 ProtoForge FINS 服务器将 w0 映射到 W 区(地址0)，
# 而 EdgeLite 配置地址 D0,w 映射到 DM 区(地址0)
# 需要将 EdgeLite 的 w0 地址改为 W0,w 或将 ProtoForge 点改名为 d0
# 检查 ProtoForge FINS 服务器中 w0 对应的区域
# 从之前的修复可知，ProtoForge FINS 支持 W 区
# EdgeLite 端地址 D0,w 表示 DM区偏移0字
# 但 ProtoForge 的 w0 点名 -> FINS 服务器可能映射到 W 区
# 解决方案: 将 EdgeLite 的 w0 地址改为 W0,w

# 更新 EdgeLite pf-fins 的 w0 点地址
print("  更新 EdgeLite pf-fins w0 地址: D0,w -> W0,w")
code, data = api(EL, el_token, "GET", "/devices/pf-fins")
if code == 200 and data:
    d = data.get("data", data)
    points = d.get("points", [])
    # 更新 w0 的地址
    for p in points:
        if p.get("name") == "w0":
            p["address"] = "W0,w"
            break
    # 发送更新
    update_body = {
        "name": d.get("name"),
        "protocol": d.get("protocol"),
        "config": d.get("config"),
        "collect_interval": d.get("collect_interval"),
        "points": points,
    }
    code2, data2 = api(EL, el_token, "PUT", "/devices/pf-fins", update_body)
    print(f"  更新结果: HTTP {code2}: {json.dumps(data2, ensure_ascii=False)[:200]}")

# 写入特征值到 ProtoForge
code, data = api(PF, pf_token, "PUT", "/devices/pf-fins/points/w0", {"value": 1234})
print(f"  写入 ProtoForge w0=1234: HTTP {code}")

# ===================================================================
# 5. 修复 pf-mqtt: 检查并修复订阅 topic
# ===================================================================
print("\n=== 5. 检查 pf-mqtt 订阅 ===")
# EdgeLite pf-mqtt 的 total_reads=0，说明从未收到消息
# 检查 ProtoForge MQTT 发布的 topic 格式
# ProtoForge 应该发布到 protoforge/pf-mqtt/temp
# EdgeLite 订阅 protoforge/#，应该能收到
# 但 total_reads=0 可能是因为 MQTT broker 没运行或连接失败

# 写入特征值
code, data = api(PF, pf_token, "PUT", "/devices/pf-mqtt/points/temp", {"value": 36.6})
print(f"  写入 ProtoForge pf-mqtt/temp=36.6: HTTP {code}")

# 检查 MQTT broker 是否在运行
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(("127.0.0.1", 1883))
    print("  MQTT broker (1883): 可达")
    s.close()
except Exception as e:
    print(f"  MQTT broker (1883): 不可达 - {e}")

# ===================================================================
# 6. 启动 ProtoForge AB 协议
# ===================================================================
print("\n=== 6. 启动 ProtoForge AB 协议 ===")
code, data = api(PF, pf_token, "POST", "/protocols/ab/start")
print(f"  启动 AB: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")

# ===================================================================
# 7. 在 EdgeLite 创建缺失的设备
# ===================================================================
print("\n=== 7. 创建 EdgeLite 缺失设备 ===")

# 7a. 创建 pf-mc
code, data = api(EL, el_token, "GET", "/devices/pf-mc")
if code == 404:
    mc_dev = {
        "device_id": "pf-mc",
        "name": "PF Mitsubishi MC",
        "protocol": "mitsubishi_mc",
        "config": {
            "host": "127.0.0.1",
            "port": 5000,
            "plc_type": "Q",
            "frame_type": "3E",
            "timeout": 5,
        },
        "collect_interval": 5,
        "points": [
            {"name": "d0", "data_type": "int16", "address": "D0", "access_mode": "rw"},
        ],
    }
    code, data = api(EL, el_token, "POST", "/devices", mc_dev)
    print(f"  创建 pf-mc: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"  pf-mc 已存在: HTTP {code}")

# 7b. 创建 pf-opcua
code, data = api(EL, el_token, "GET", "/devices/pf-opcua")
if code == 404:
    opcua_dev = {
        "device_id": "pf-opcua",
        "name": "PF OPC UA",
        "protocol": "opcua",
        "config": {
            "url": "opc.tcp://127.0.0.1:4840",
            "security_mode": "none",
            "timeout": 5,
        },
        "collect_interval": 5,
        "points": [
            {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=motor_speed", "access_mode": "rw"},
            {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=valve_open", "access_mode": "rw"},
        ],
    }
    code, data = api(EL, el_token, "POST", "/devices", opcua_dev)
    print(f"  创建 pf-opcua: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"  pf-opcua 已存在: HTTP {code}")
    # 更新点位
    if code == 200:
        d = data.get("data", data)
        points = [
            {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=motor_speed", "access_mode": "rw"},
            {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=valve_open", "access_mode": "rw"},
        ]
        update_body = {
            "name": d.get("name"),
            "protocol": d.get("protocol"),
            "config": d.get("config"),
            "collect_interval": d.get("collect_interval"),
            "points": points,
        }
        code2, data2 = api(EL, el_token, "PUT", "/devices/pf-opcua", update_body)
        print(f"  更新 pf-opcua 点位: HTTP {code2}")

# 7c. 创建 pf-http
code, data = api(EL, el_token, "GET", "/devices/pf-http")
if code == 404:
    http_dev = {
        "device_id": "pf-http",
        "name": "PF HTTP Webhook",
        "protocol": "http_webhook",
        "config": {
            "url": "http://127.0.0.1:8180/api/v1/webhook/http",
            "method": "POST",
            "timeout": 10,
        },
        "collect_interval": 5,
        "points": [
            {"name": "temperature", "data_type": "float32", "address": "temperature", "access_mode": "rw"},
            {"name": "pressure", "data_type": "float32", "address": "pressure", "access_mode": "rw"},
        ],
    }
    code, data = api(EL, el_token, "POST", "/devices", http_dev)
    print(f"  创建 pf-http: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"  pf-http 已存在: HTTP {code}")

# ===================================================================
# 8. 修复 pf-s7: 地址映射冲突
# ===================================================================
print("\n=== 8. 检查 pf-s7 地址冲突 ===")
# ProtoForge S7 服务器在端口 102 上同时有 pf-s7 和 jt-s7
# pf-s7: temp=DB1.D0(float32), word1=DB1.W4(int16)
# jt-s7: temperature(DB1.DBD0?), pressure, speed, running
# 它们都使用 DB1，地址重叠！
# EdgeLite pf-s7 读到 temp=74.98 对应 jt-s7 的 temperature 值
# 解决方案: 将 pf-s7 的点地址改到不冲突的 DB号或偏移
code, data = api(EL, el_token, "GET", "/devices/pf-s7")
if code == 200 and data:
    d = data.get("data", data)
    points = d.get("points", [])
    # 将 pf-s7 的地址改到 DB2，避免与 jt-s7(DB1) 冲突
    for p in points:
        if p.get("name") == "temp":
            p["address"] = "DB2.D0"  # float32 at DB2 offset 0
        elif p.get("name") == "word1":
            p["address"] = "DB2.W4"  # int16 at DB2 offset 4
        elif p.get("name") == "bit1":
            p["address"] = "DB2.X6.0"  # bool at DB2 offset 6 bit 0
        elif p.get("name") == "bit2":
            p["address"] = "M20.0"  # M区不冲突
    update_body = {
        "name": d.get("name"),
        "protocol": d.get("protocol"),
        "config": d.get("config"),
        "collect_interval": d.get("collect_interval"),
        "points": points,
    }
    code2, data2 = api(EL, el_token, "PUT", "/devices/pf-s7", update_body)
    print(f"  更新 pf-s7 地址到 DB2: HTTP {code2}")

    # 同时需要确保 ProtoForge 的 pf-s7 也在 DB2 创建了对应数据
    # ProtoForge 的 S7 服务器应该根据设备点位配置自动创建 DB
    # 写入特征值
    code3, data3 = api(PF, pf_token, "PUT", "/devices/pf-s7/points/temp", {"value": 12.5})
    print(f"  写入 pf-s7/temp=12.5: HTTP {code3}")
    code4, data4 = api(PF, pf_token, "PUT", "/devices/pf-s7/points/word1", {"value": 1000})
    print(f"  写入 pf-s7/word1=1000: HTTP {code4}")

# 等待采集周期
print("\n等待采集周期 (15s)...")
time.sleep(15)

# 验证修复结果
print("\n=== 验证修复结果 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = api(EL, el_token, "GET", f"/devices/{dev_id}/points")
    if code == 200 and data:
        points = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(points, dict):
            vals = {k: v.get("value") if isinstance(v, dict) else v for k, v in points.items()}
            print(f"  {dev_id}: {vals}")
        else:
            print(f"  {dev_id}: {points}")
    else:
        print(f"  {dev_id}: HTTP {code}")
