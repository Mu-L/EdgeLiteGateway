#!/usr/bin/env python3
"""修复 AB 的 ip 字段和 OPC UA 的 NodeId 路径。"""
import json
import time
import urllib.request
import urllib.error

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


el = Client(EL, "admin", "EdgeLite@2026")
el.login()

# 1. 修复 pf-ab: 使用 ip 字段替代 host
print("=== 1. 修复 pf-ab ===")
el.delete("/devices/pf-ab")
time.sleep(2)
ab_dev = {
    "device_id": "pf-ab", "name": "PF AB", "protocol": "allen_bradley",
    "config": {"ip": "127.0.0.1", "port": 44818, "timeout": 5},
    "collect_interval": 5,
    "points": [
        {"name": "Temperature", "data_type": "float32", "address": "Temperature", "access_mode": "rw"},
        {"name": "Setpoint", "data_type": "float32", "address": "Setpoint", "access_mode": "rw"},
    ],
}
code, data = el.post("/devices", ab_dev)
print(f"  创建 pf-ab: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200] if data else ''}")

# 2. 修复 pf-opcua: NodeId 改回 ns=2;s=motor_speed（不带设备ID前缀）
print("\n=== 2. 修复 pf-opcua NodeId ===")
el.delete("/devices/pf-opcua")
time.sleep(2)
opcua_dev = {
    "device_id": "pf-opcua", "name": "PF OPC UA", "protocol": "opcua",
    "config": {"endpoint": "opc.tcp://127.0.0.1:4840", "security_mode": "None", "timeout": 5},
    "collect_interval": 5,
    "points": [
        {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=motor_speed", "access_mode": "rw"},
        {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=valve_open", "access_mode": "rw"},
    ],
}
code, data = el.post("/devices", opcua_dev)
print(f"  创建 pf-opcua: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200] if data else ''}")

# 3. 重启 pf-mc（连接失败）
print("\n=== 3. 重新创建 pf-mc ===")
el.delete("/devices/pf-mc")
time.sleep(2)
mc_dev = {
    "device_id": "pf-mc", "name": "PF MC", "protocol": "mitsubishi_mc",
    "config": {"host": "127.0.0.1", "port": 5000, "timeout": 5},
    "collect_interval": 5,
    "points": [
        {"name": "d0", "data_type": "int16", "address": "D0", "access_mode": "rw"},
    ],
}
code, data = el.post("/devices", mc_dev)
print(f"  创建 pf-mc: HTTP {code}")

# 4. 重新创建 pf-mqtt（reads=0 可能是连接问题）
print("\n=== 4. 重新创建 pf-mqtt ===")
el.delete("/devices/pf-mqtt")
time.sleep(2)
mqtt_dev = {
    "device_id": "pf-mqtt", "name": "PF MQTT", "protocol": "mqtt_client",
    "config": {
        "broker": "127.0.0.1", "port": 1883,
        "subscribe_topic": "protoforge/#",
        "publish_topic": "protoforge/command",
        "client_id": "pf-mqtt-el8",
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

# 等待驱动连接
print("\n等待驱动连接 (30s)...")
time.sleep(30)

# 5. 验证
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
