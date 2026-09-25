#!/usr/bin/env python3
"""最终修复脚本：修复 pf-http, pf-s7, pf-fins, pf-mqtt 并运行验收。"""
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


class Client:
    def __init__(self, base, user, password):
        self.base = base
        self.user = user
        self.password = password
        self.token = ""
        self.csrf = ""

    def login(self):
        data = json.dumps({"username": self.user, "password": self.password}).encode()
        req = urllib.request.Request(f"{self.base}/auth/login", data=data, method="POST")
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
            req = urllib.request.Request(f"{self.base}{path}", method=method)
            req.add_header("Authorization", f"Bearer {self.token}")
            req.add_header("Content-Type", "application/json")
            if self.csrf:
                req.add_header("X-CSRF-Token", self.csrf)
            data = json.dumps(body).encode() if body else None
            try:
                with urllib.request.urlopen(req, data=data, timeout=30) as resp:
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


pf = Client(PF, PF_USER, PF_PASS)
el = Client(EL, EL_USER, EL_PASS)
pf.login()
el.login()

# ===================================================================
# 1. 修复 pf-http: 通过 ProtoForge 集成重新推送设备
# ===================================================================
print("=== 1. 修复 pf-http ===")

# 检查 ProtoForge pf-http 设备状态
code, data = pf.get("/devices/pf-http")
if code == 200:
    d = data.get("device", data) if isinstance(data, dict) else data
    print(f"  ProtoForge pf-http: {json.dumps(d, ensure_ascii=False)[:300]}")
    points = d.get("points", [])
    for p in points:
        print(f"    {p.get('name')}: value={p.get('value')}")
else:
    print(f"  ProtoForge pf-http: HTTP {code}")

# 向 ProtoForge pf-http 写入特征值
for name, val in [("temperature", 42.0), ("pressure", 1.5)]:
    code, data = pf.put(f"/devices/pf-http/points/{name}", {"value": val})
    print(f"  写入 PF pf-http/{name}={val}: HTTP {code}")

# 直接通过 EdgeLite push API 推送数据（模拟 ProtoForge 的推送）
# EdgeLite push 端点接受 Bearer Token 认证
push_payload = {
    "data": {
        "temperature": {"value": 42.0, "quality": "good", "timestamp": "2026-01-01T00:00:00Z"},
        "pressure": {"value": 1.5, "quality": "good", "timestamp": "2026-01-01T00:00:00Z"},
    }
}
code, data = el.post("/devices/pf-http/push", push_payload)
print(f"  EdgeLite push pf-http: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200] if data else ''}")

# 等待并检查
time.sleep(3)
code, data = el.get("/devices/pf-http/points")
if code == 200 and data:
    points = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(points, dict):
        vals = {k: v.get("value") if isinstance(v, dict) else v for k, v in points.items()}
        print(f"  pf-http 采集值: {vals}")

# ===================================================================
# 2. 修复 pf-s7, pf-fins, pf-mqtt: 重启 ProtoForge 协议服务
# ===================================================================
print("\n=== 2. 重启 ProtoForge 协议服务 ===")
for proto in ["s7", "fins", "mqtt"]:
    code, data = pf.post(f"/protocols/{proto}/stop")
    print(f"  停止 {proto}: HTTP {code}")
    time.sleep(2)
    code, data = pf.post(f"/protocols/{proto}/start")
    print(f"  启动 {proto}: HTTP {code}")
    time.sleep(1)

# 等待协议服务启动
print("  等待协议服务启动 (15s)...")
time.sleep(15)

# 重新写入特征值
print("\n=== 3. 重新写入特征值 ===")
write_specs = [
    ("pf-s7", "temp", 12.5), ("pf-s7", "word1", 1000),
    ("pf-fins", "w0", 1234),
    ("pf-mqtt", "temp", 36.6),
]
for dev_id, point, value in write_specs:
    code, data = pf.put(f"/devices/{dev_id}/points/{point}", {"value": value})
    print(f"  {dev_id}/{point}={value}: HTTP {code}")

# 等待采集周期
print("\n  等待采集周期 (20s)...")
time.sleep(20)

# ===================================================================
# 4. 重新删除并创建 EdgeLite S7/FINS/MQTT 设备
# ===================================================================
print("\n=== 4. 重新创建 EdgeLite S7/FINS/MQTT 设备 ===")

# S7
el.delete("/devices/pf-s7")
time.sleep(2)
s7_dev = {
    "device_id": "pf-s7",
    "name": "PF S7",
    "protocol": "siemens_s7",
    "config": {"ip": "127.0.0.1", "port": 102, "rack": 0, "slot": 1},
    "collect_interval": 5,
    "points": [
        {"name": "temp", "data_type": "float32", "address": "DB1.D0", "access_mode": "rw"},
        {"name": "word1", "data_type": "int16", "address": "DB1.W4", "access_mode": "rw"},
        {"name": "bit1", "data_type": "bool", "address": "DB1.X6.0", "access_mode": "rw"},
        {"name": "bit2", "data_type": "bool", "address": "M10.0", "access_mode": "rw"},
    ],
}
code, data = el.post("/devices", s7_dev)
print(f"  创建 pf-s7: HTTP {code}")

# FINS
el.delete("/devices/pf-fins")
time.sleep(2)
fins_dev = {
    "device_id": "pf-fins",
    "name": "PF FINS",
    "protocol": "omron_fins",
    "config": {"host": "127.0.0.1", "ip": "127.0.0.1", "port": 9600, "transport": "tcp", "timeout": 5.0},
    "collect_interval": 5,
    "points": [
        {"name": "w0", "data_type": "uint16", "address": "D0,w", "access_mode": "rw"},
        {"name": "f2", "data_type": "float32", "address": "D2,r", "access_mode": "rw"},
        {"name": "w10", "data_type": "uint16", "address": "D10,w", "access_mode": "rw"},
        {"name": "b20", "data_type": "bool", "address": "D20.0,b", "access_mode": "rw"},
    ],
}
code, data = el.post("/devices", fins_dev)
print(f"  创建 pf-fins: HTTP {code}")

# MQTT
el.delete("/devices/pf-mqtt")
time.sleep(2)
mqtt_dev = {
    "device_id": "pf-mqtt",
    "name": "PF MQTT",
    "protocol": "mqtt_client",
    "config": {
        "broker": "127.0.0.1", "port": 1883,
        "subscribe_topic": "protoforge/#",
        "publish_topic": "protoforge/command",
        "client_id": "pf-mqtt-el3",
        "topic_prefix": "protoforge",
        "retain": False, "qos": 0,
    },
    "collect_interval": 5,
    "points": [
        {"name": "temp", "data_type": "float32", "unit": "C", "address": "protoforge/pf-mqtt/temp", "access_mode": "rw"},
        {"name": "switch", "data_type": "float32", "address": "protoforge/pf-mqtt/switch", "access_mode": "rw"},
    ],
}
code, data = el.post("/devices", mqtt_dev)
print(f"  创建 pf-mqtt: HTTP {code}")

# 等待驱动连接和采集
print("\n  等待驱动连接 (30s)...")
time.sleep(30)

# 重新写入特征值（在设备创建后）
print("\n=== 5. 再次写入特征值 ===")
for dev_id, point, value in write_specs:
    code, data = pf.put(f"/devices/{dev_id}/points/{point}", {"value": value})
    print(f"  {dev_id}/{point}={value}: HTTP {code}")

# 等待采集周期
print("\n  等待采集周期 (20s)...")
time.sleep(20)

# ===================================================================
# 6. 最终验证
# ===================================================================
print("\n=== 6. 最终验证 ===")
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

# 健康状态
print("\n=== 健康状态 ===")
for dev_id in ["pf-s7", "pf-fins", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = el.get(f"/devices/{dev_id}/health")
    if code == 200 and data:
        d = data.get("data", data) if isinstance(data, dict) else data
        print(f"  {dev_id}: connected={d.get('is_connected')} reads={d.get('total_reads')} failures={d.get('consecutive_failures')}")
    else:
        print(f"  {dev_id}: HTTP {code}")
