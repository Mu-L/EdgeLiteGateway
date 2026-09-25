#!/usr/bin/env python3
"""修复脚本3：修复 pf-s7 地址格式、pf-fins 地址、pf-opcua 配置、pf-mqtt。"""
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


class ELClient:
    def __init__(self):
        self.token = ""
        self.csrf = ""

    def login(self):
        data = json.dumps({"username": EL_USER, "password": EL_PASS}).encode()
        req = urllib.request.Request(f"{EL}/auth/login", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.load(resp)
        payload = body.get("data") if isinstance(body.get("data"), dict) else body
        self.token = payload["access_token"]
        self.csrf = resp.headers.get("X-CSRF-Token", "")

    def request(self, method, path, body=None):
        if not self.token:
            self.login()
        for attempt in (1, 2):
            req = urllib.request.Request(f"{EL}{path}", method=method)
            req.add_header("Authorization", f"Bearer {self.token}")
            req.add_header("Content-Type", "application/json")
            if self.csrf:
                req.add_header("X-CSRF-Token", self.csrf)
            data = json.dumps(body).encode() if body else None
            try:
                with urllib.request.urlopen(req, data=data, timeout=20) as resp:
                    raw = resp.read().decode()
                    new_csrf = resp.headers.get("X-CSRF-Token")
                    if new_csrf:
                        self.csrf = new_csrf
                    return resp.status, (json.loads(raw) if raw else None)
            except urllib.error.HTTPError as e:
                raw = e.read().decode()
                try:
                    payload = json.loads(raw)
                except Exception:
                    payload = {"raw": raw[:500]}
                if e.code == 403 and "csrf" in raw.lower():
                    new_csrf = payload.get("csrf_token")
                    if new_csrf:
                        self.csrf = new_csrf
                        if attempt == 1:
                            continue
                if e.code == 401 and attempt == 1:
                    self.login()
                    continue
                return e.code, payload
        raise RuntimeError("unreachable")

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, body=None):
        return self.request("POST", path, body or {})

    def put(self, path, body=None):
        return self.request("PUT", path, body or {})

    def delete(self, path):
        return self.request("DELETE", path)


def pf_login():
    data = json.dumps({"username": PF_USER, "password": PF_PASS}).encode()
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
        with urllib.request.urlopen(req, data=data, timeout=20) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:500]}


pf_token = pf_login()
el = ELClient()
el.login()

# ===================================================================
# 1. 修复 pf-s7: 检查 EdgeLite S7 驱动支持的地址格式
# ===================================================================
print("=== 1. 修复 pf-s7 地址格式 ===")
# 之前地址 DB1.D0 -> 读到 jt-s7 的值
# 改为 DB1.DBD0 -> 读到 None（可能不兼容此格式）
# 需要检查 EdgeLite S7 驱动支持什么地址格式

# 先恢复原来的地址格式，但改用不同 DB 号
# 检查 ProtoForge S7 服务器如何为 pf-s7 分配 DB
# ProtoForge 的 pf-s7 原始配置:
#   temp: DB1.D0 (float32)
#   word1: DB1.W4 (int16)
#   bit1: DB1.X6.0 (bool)
#   bit2: M10.0 (bool)

# jt-s7 可能也在用 DB1:
#   temperature: DB1.D0 (float32) -> 与 pf-s7 的 temp 冲突!

# 解决方案: 在 ProtoForge 中修改 pf-s7 的点位地址，使用不同 DB 号
# 或者: 在 EdgeLite 中修改 pf-s7 的地址到 DB2
# 但需要 ProtoForge S7 服务器也支持 DB2

# 检查 ProtoForge pf-s7 的点地址
code, data = pf_api(pf_token, "GET", "/devices/pf-s7")
if code == 200:
    d = data.get("device", data)
    print(f"  ProtoForge pf-s7 点位:")
    for p in d.get("points", []):
        print(f"    {p.get('name')}: value={p.get('value')}")

# 检查 ProtoForge jt-s7 的点地址
code, data = pf_api(pf_token, "GET", "/devices/jt-s7")
if code == 200:
    d = data.get("device", data)
    print(f"  ProtoForge jt-s7 点位:")
    for p in d.get("points", []):
        print(f"    {p.get('name')}: value={p.get('value')}")

# ProtoForge S7 服务器可能按设备名分配 DB
# 尝试在 EdgeLite 恢复原始地址格式 DB1.D0
code, data = el.get("/devices/pf-s7")
if code == 200 and data:
    d = data.get("data", data)
    points = d.get("points", [])
    # 恢复原始地址
    for p in points:
        if p.get("name") == "temp":
            p["address"] = "DB1.D0"  # 恢复原始格式
        elif p.get("name") == "word1":
            p["address"] = "DB1.W4"
        elif p.get("name") == "bit1":
            p["address"] = "DB1.X6.0"
        elif p.get("name") == "bit2":
            p["address"] = "M10.0"
    update_body = {
        "name": d.get("name"),
        "protocol": d.get("protocol"),
        "config": d.get("config"),
        "collect_interval": d.get("collect_interval"),
        "points": points,
    }
    code2, data2 = el.put("/devices/pf-s7", update_body)
    print(f"  恢复 pf-s7 地址: HTTP {code2}")

# ===================================================================
# 2. 修复 pf-fins: 检查 W0 地址是否正确
# ===================================================================
print("\n=== 2. 检查 pf-fins 地址 ===")
# EdgeLite w0 地址改为 W0,w，但读到 0
# ProtoForge pf-fins 的 w0 点名 -> FINS 服务器映射
# 可能 ProtoForge FINS 服务器将 w0 映射到 W 区地址 0
# EdgeLite 地址 W0,w 表示 W 区偏移 0 字
# 但 FINS 协议 W 区的标准字区码是 0xB1
# EdgeLite 驱动可能使用非标准区码 0xB4
# ProtoForge 之前已修复了区码别名映射
# 检查 EdgeLite 读到的值
code, data = el.get("/devices/pf-fins/points")
if code == 200 and data:
    points = data.get("data", data) if isinstance(data, dict) else data
    print(f"  EdgeLite pf-fins 点位: {points}")

# 写入特征值
code, data = pf_api(pf_token, "PUT", "/devices/pf-fins/points/w0", {"value": 1234})
print(f"  写入 ProtoForge pf-fins/w0=1234: HTTP {code}")

# 也可以检查 ProtoForge FINS 服务器中的实际值
# 使用裸 FINS 帧读取 W0
import socket as _socket
import struct as _struct

def fins_read_w0(port=9600):
    """直读 FINS W0 字地址"""
    def recv_exact(s, n):
        buf = b""
        while len(buf) < n:
            c = s.recv(n - len(buf))
            if not c:
                raise ConnectionError("closed")
            buf += c
        return buf

    def recv_frame(s):
        h = recv_exact(s, 8)
        return recv_exact(s, _struct.unpack(">I", h[4:8])[0])

    s = _socket.create_connection(("127.0.0.1", port), timeout=5)
    try:
        # FINS/TCP 握手
        init = _struct.pack(">I", 0) + _struct.pack(">I", 0) + _struct.pack(">I", 0)
        s.sendall(b"FINS" + _struct.pack(">I", len(init)) + init)
        recv_frame(s)
        # 读 W0 (区码 0xB1 = WR word, 偏移 0, 1个字)
        fins_hdr = bytes([0x80, 0, 2, 0, 1, 0, 0, 0, 0, 1])
        # FINS 命令: 0101 (读), 区码 0xB1 (WR word), 偏移 0, 数量 1
        data = bytes([0xB1]) + _struct.pack(">H", 0) + bytes([0]) + _struct.pack(">H", 1)
        body = _struct.pack(">I", 2) + _struct.pack(">I", 0) + fins_hdr + bytes([0x01, 0x01]) + data
        s.sendall(b"FINS" + _struct.pack(">I", len(body)) + body)
        r = recv_frame(s)
        print(f"  FINS W0 直读响应: {r.hex()} (len={len(r)})")
        if len(r) >= 24:
            val = int.from_bytes(r[22:24], "big")
            print(f"  FINS W0 直读值: {val}")
            return val
        return None
    finally:
        s.close()

try:
    fins_read_w0()
except Exception as e:
    print(f"  FINS 直读失败: {e}")

# 也尝试读 D0 (DM 区)
def fins_read_d0(port=9600):
    """直读 FINS D0 字地址"""
    def recv_exact(s, n):
        buf = b""
        while len(buf) < n:
            c = s.recv(n - len(buf))
            if not c:
                raise ConnectionError("closed")
            buf += c
        return buf

    def recv_frame(s):
        h = recv_exact(s, 8)
        return recv_exact(s, _struct.unpack(">I", h[4:8])[0])

    s = _socket.create_connection(("127.0.0.1", port), timeout=5)
    try:
        init = _struct.pack(">I", 0) + _struct.pack(">I", 0) + _struct.pack(">I", 0)
        s.sendall(b"FINS" + _struct.pack(">I", len(init)) + init)
        recv_frame(s)
        # 读 D0 (区码 0x82 = DM word, 偏移 0, 1个字)
        fins_hdr = bytes([0x80, 0, 2, 0, 1, 0, 0, 0, 0, 1])
        data = bytes([0x82]) + _struct.pack(">H", 0) + bytes([0]) + _struct.pack(">H", 1)
        body = _struct.pack(">I", 2) + _struct.pack(">I", 0) + fins_hdr + bytes([0x01, 0x01]) + data
        s.sendall(b"FINS" + _struct.pack(">I", len(body)) + body)
        r = recv_frame(s)
        print(f"  FINS D0 直读响应: {r.hex()} (len={len(r)})")
        if len(r) >= 24:
            val = int.from_bytes(r[22:24], "big")
            print(f"  FINS D0 直读值: {val}")
            return val
        return None
    finally:
        s.close()

try:
    fins_read_d0()
except Exception as e:
    print(f"  FINS D0 直读失败: {e}")

# ===================================================================
# 3. 修复 pf-opcua: 使用正确的配置字段名
# ===================================================================
print("\n=== 3. 创建 EdgeLite pf-opcua ===")
# 422 错误: protocol 'opc_ua' 的 config 需要 endpoint_url
code, data = el.get("/devices/pf-opcua")
if code == 404:
    opcua_dev = {
        "device_id": "pf-opcua",
        "name": "PF OPC UA",
        "protocol": "opcua",
        "config": {
            "endpoint_url": "opc.tcp://127.0.0.1:4840",
            "security_mode": "none",
            "timeout": 5,
        },
        "collect_interval": 5,
        "points": [
            {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=motor_speed", "access_mode": "rw"},
            {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=valve_open", "access_mode": "rw"},
        ],
    }
    code, data = el.post("/devices", opcua_dev)
    print(f"  创建 pf-opcua: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:300]}")
else:
    print(f"  pf-opcua 已存在: HTTP {code}")
    if code == 200:
        d = data.get("data", data)
        config = d.get("config", {})
        if "endpoint_url" not in config:
            config["endpoint_url"] = "opc.tcp://127.0.0.1:4840"
        points = [
            {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=motor_speed", "access_mode": "rw"},
            {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=valve_open", "access_mode": "rw"},
        ]
        update_body = {
            "name": d.get("name"),
            "protocol": d.get("protocol"),
            "config": config,
            "collect_interval": d.get("collect_interval"),
            "points": points,
        }
        code2, data2 = el.put("/devices/pf-opcua", update_body)
        print(f"  更新 pf-opcua: HTTP {code2}")

# ===================================================================
# 4. 修复 pf-mqtt: 检查 ProtoForge MQTT 发布是否到达 broker
# ===================================================================
print("\n=== 4. 检查 pf-mqtt ===")
# ProtoForge pf-mqtt/temp=36.6，MQTT broker 可达
# 但 EdgeLite total_reads=0
# 可能原因: EdgeLite MQTT 驱动连接 broker 但未订阅正确 topic
# 或 ProtoForge 发布的 topic 与 EdgeLite 订阅的不匹配

# 检查 ProtoForge 发布的 topic 格式
# ProtoForge 应该发布到 protoforge/pf-mqtt/temp
# EdgeLite 订阅 protoforge/# 应该能匹配

# 让我检查 EdgeLite MQTT 驱动的日志
# 先用 mqtt 客户端监听确认 ProtoForge 是否在发布
try:
    import paho.mqtt.client as mqtt_lib
    received = []

    def on_message(client, userdata, msg):
        received.append({"topic": msg.topic, "payload": msg.payload.decode()})

    client = mqtt_lib.Client()
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, 60)
    client.subscribe("protoforge/#")
    client.loop_start()
    time.sleep(5)
    client.loop_stop()
    client.disconnect()
    print(f"  MQTT 监听 protoforge/# 收到 {len(received)} 条消息:")
    for r in received:
        print(f"    topic={r['topic']} payload={r['payload'][:100]}")
except ImportError:
    print("  paho-mqtt 未安装，跳过监听")
except Exception as e:
    print(f"  MQTT 监听失败: {e}")

# ===================================================================
# 5. 修复 pf-http: 检查 webhook 配置
# ===================================================================
print("\n=== 5. 检查 pf-http ===")
code, data = el.get("/devices/pf-http")
if code == 200 and data:
    d = data.get("data", data)
    config = d.get("config", {})
    print(f"  配置: {json.dumps(config, ensure_ascii=False)}")
    points = d.get("points", [])
    print(f"  点位: {points}")

# ===================================================================
# 6. 检查 EdgeLite S7 驱动的地址解析
# ===================================================================
print("\n=== 6. 检查 EdgeLite S7 驱动地址解析 ===")
# 查看 EdgeLite S7 驱动支持的地址格式
code, data = el.get("/devices/pf-s7")
if code == 200 and data:
    d = data.get("data", data)
    points = d.get("points", [])
    print(f"  pf-s7 当前点位:")
    for p in points:
        print(f"    {p.get('name')}: addr={p.get('address')} type={p.get('data_type')}")

# 等待采集周期
print("\n等待采集周期 (15s)...")
time.sleep(15)

# 验证
print("\n=== 验证修复结果 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = el.get(f"/devices/{dev_id}/points")
    if code == 200 and data:
        points = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(points, dict):
            vals = {k: v.get("value") if isinstance(v, dict) else v for k, v in points.items()}
            print(f"  {dev_id}: {vals}")
        else:
            print(f"  {dev_id}: {points}")
    else:
        print(f"  {dev_id}: HTTP {code}")
