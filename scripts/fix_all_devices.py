#!/usr/bin/env python3
"""综合修复脚本：重新登录、重建 EdgeLite 设备、写入特征值、验证采集。"""
import json
import time
import urllib.request
import urllib.error

PF = "http://127.0.0.1:8000/api/v1"
EL = "http://127.0.0.1:8180/api/v1"


class Client:
    def __init__(self, base, user, password):
        self.base = base
        self.user = user
        self.password = password
        self.token = ""
        self.csrf = ""

    def login(self):
        data = json.dumps({"username": self.user, "password": self.password, "no_revoke": True}).encode()
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


pf = Client(PF, "admin", "admin")
el = Client(EL, "admin", "EdgeLite@2026")
pf.login()
el.login()

# ===================================================================
# 1. 向 ProtoForge 写入所有特征值
# ===================================================================
print("=== 1. 向 ProtoForge 写入特征值 ===")
WRITE_SPECS = [
    ("pf-modbus", "temp", 66.6), ("pf-modbus", "word1", 4321),
    ("pf-s7", "temp", 12.5), ("pf-s7", "word1", 1000),
    ("pf-mc", "d0", 555),
    ("pf-fins", "w0", 1234),
    ("pf-ab", "Temperature", 26.5),
    ("pf-mqtt", "temp", 36.6),
    ("pf-opcua", "motor_speed", 1500), ("pf-opcua", "valve_open", True),
    ("pf-http", "temperature", 42.0), ("pf-http", "pressure", 1.5),
]
for dev_id, point, value in WRITE_SPECS:
    code, data = pf.put(f"/devices/{dev_id}/points/{point}", {"value": value})
    print(f"  {dev_id}/{point}={value}: HTTP {code}")

# ===================================================================
# 2. 删除并重新创建 EdgeLite 所有设备（确保配置正确）
# ===================================================================
print("\n=== 2. 重新创建 EdgeLite 设备 ===")

DEVICE_CONFIGS = {
    "pf-modbus": {
        "device_id": "pf-modbus", "name": "PF Modbus TCP", "protocol": "modbus_tcp",
        "config": {"host": "127.0.0.1", "port": 5020, "slave_id": 1, "timeout": 5},
        "collect_interval": 5,
        "points": [
            {"name": "temp", "data_type": "float32", "address": "HR100", "access_mode": "rw"},
            {"name": "word1", "data_type": "int16", "address": "HR102", "access_mode": "rw"},
            {"name": "coil1", "data_type": "bool", "address": "C0", "access_mode": "rw"},
            {"name": "coil2", "data_type": "bool", "address": "C1", "access_mode": "rw"},
            {"name": "di1", "data_type": "bool", "address": "I0", "access_mode": "r"},
            {"name": "speed", "data_type": "int16", "address": "HR104", "access_mode": "rw"},
        ],
    },
    "pf-s7": {
        "device_id": "pf-s7", "name": "PF S7", "protocol": "siemens_s7",
        "config": {"ip": "127.0.0.1", "port": 102, "rack": 0, "slot": 1},
        "collect_interval": 5,
        "points": [
            {"name": "temp", "data_type": "float32", "address": "DB1.D0", "access_mode": "rw"},
            {"name": "word1", "data_type": "int16", "address": "DB1.W4", "access_mode": "rw"},
            {"name": "bit1", "data_type": "bool", "address": "DB1.X6.0", "access_mode": "rw"},
            {"name": "bit2", "data_type": "bool", "address": "M10.0", "access_mode": "rw"},
        ],
    },
    "pf-mc": {
        "device_id": "pf-mc", "name": "PF MC", "protocol": "mitsubishi_mc",
        "config": {"host": "127.0.0.1", "port": 5000, "timeout": 5},
        "collect_interval": 5,
        "points": [
            {"name": "d0", "data_type": "int16", "address": "D0", "access_mode": "rw"},
        ],
    },
    "pf-fins": {
        "device_id": "pf-fins", "name": "PF FINS", "protocol": "omron_fins",
        "config": {"host": "127.0.0.1", "ip": "127.0.0.1", "port": 9600, "transport": "tcp", "timeout": 5.0},
        "collect_interval": 5,
        "points": [
            {"name": "w0", "data_type": "uint16", "address": "D0,w", "access_mode": "rw"},
            {"name": "f2", "data_type": "float32", "address": "D2,r", "access_mode": "rw"},
            {"name": "w10", "data_type": "uint16", "address": "D10,w", "access_mode": "rw"},
            {"name": "b20", "data_type": "bool", "address": "D20.0,b", "access_mode": "rw"},
        ],
    },
    "pf-ab": {
        "device_id": "pf-ab", "name": "PF AB", "protocol": "allen_bradley",
        "config": {"host": "127.0.0.1", "port": 44818, "timeout": 5},
        "collect_interval": 5,
        "points": [
            {"name": "Temperature", "data_type": "float32", "address": "Temperature", "access_mode": "rw"},
            {"name": "Setpoint", "data_type": "float32", "address": "Setpoint", "access_mode": "rw"},
        ],
    },
    "pf-mqtt": {
        "device_id": "pf-mqtt", "name": "PF MQTT", "protocol": "mqtt_client",
        "config": {
            "broker": "127.0.0.1", "port": 1883,
            "subscribe_topic": "protoforge/#",
            "publish_topic": "protoforge/command",
            "client_id": "pf-mqtt-el5",
            "topic_prefix": "protoforge",
            "retain": False, "qos": 0,
        },
        "collect_interval": 5,
        "points": [
            {"name": "temp", "data_type": "float32", "unit": "C", "address": "protoforge/pf-mqtt/temp", "access_mode": "rw"},
            {"name": "switch", "data_type": "float32", "address": "protoforge/pf-mqtt/switch", "access_mode": "rw"},
        ],
    },
    "pf-opcua": {
        "device_id": "pf-opcua", "name": "PF OPC UA", "protocol": "opcua",
        "config": {"endpoint": "opc.tcp://127.0.0.1:4840", "security_mode": "None", "timeout": 5},
        "collect_interval": 5,
        "points": [
            {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=pf-opcua.motor_speed", "access_mode": "rw"},
            {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=pf-opcua.valve_open", "access_mode": "rw"},
        ],
    },
    "pf-http": {
        "device_id": "pf-http", "name": "PF HTTP", "protocol": "http_webhook",
        "config": {"url": "http://127.0.0.1:8080/webhook/data", "method": "POST", "timeout": 10},
        "collect_interval": 5,
        "points": [
            {"name": "temperature", "data_type": "float32", "address": "temperature", "access_mode": "rw"},
            {"name": "pressure", "data_type": "float32", "address": "pressure", "access_mode": "rw"},
        ],
    },
}

for dev_id, config in DEVICE_CONFIGS.items():
    code, data = el.delete(f"/devices/{dev_id}")
    print(f"  删除 {dev_id}: HTTP {code}")
    time.sleep(1)
    code, data = el.post("/devices", config)
    print(f"  创建 {dev_id}: HTTP {code}")
    time.sleep(1)

# 等待驱动连接和采集
print("\n等待驱动连接 (30s)...")
time.sleep(30)

# ===================================================================
# 3. 再次写入特征值（设备创建后）
# ===================================================================
print("\n=== 3. 再次写入特征值 ===")
for dev_id, point, value in WRITE_SPECS:
    code, data = pf.put(f"/devices/{dev_id}/points/{point}", {"value": value})
    print(f"  {dev_id}/{point}={value}: HTTP {code}")

# 等待采集周期
print("\n等待采集周期 (15s)...")
time.sleep(15)

# ===================================================================
# 4. 推送 pf-http 数据到 EdgeLite
# ===================================================================
print("\n=== 4. 推送 pf-http 数据 ===")
push_payload = {
    "data": {
        "temperature": {"value": 42.0, "quality": "good", "timestamp": "2026-01-01T00:00:00Z"},
        "pressure": {"value": 1.5, "quality": "good", "timestamp": "2026-01-01T00:00:00Z"},
    }
}
code, data = el.post("/devices/pf-http/push", push_payload)
print(f"  push pf-http: HTTP {code}")

# ===================================================================
# 5. 验证所有设备
# ===================================================================
print("\n=== 5. 验证所有设备 ===")
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
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = el.get(f"/devices/{dev_id}/health")
    if code == 200 and data:
        d = data.get("data", data) if isinstance(data, dict) else data
        print(f"  {dev_id}: connected={d.get('is_connected')} reads={d.get('total_reads')} failures={d.get('consecutive_failures')}")
    else:
        print(f"  {dev_id}: HTTP {code}")
