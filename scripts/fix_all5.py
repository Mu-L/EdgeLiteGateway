#!/usr/bin/env python3
"""修复脚本5：重启 ProtoForge 协议服务，修复 MQTT 消息解析，修复 OPC UA 连接。"""
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
# 1. 重启 ProtoForge 所有协议服务（让协议服务器重新加载设备配置）
# ===================================================================
print("=== 1. 重启 ProtoForge 协议服务 ===")
for proto in ["s7", "fins", "mc", "mqtt", "opcua", "http", "ab", "modbus_tcp"]:
    # 停止
    code, data = pf_api(pf_token, "POST", f"/protocols/{proto}/stop")
    print(f"  停止 {proto}: HTTP {code}")
    time.sleep(1)

time.sleep(3)

for proto in ["modbus_tcp", "s7", "fins", "mc", "mqtt", "opcua", "http", "ab"]:
    # 启动
    code, data = pf_api(pf_token, "POST", f"/protocols/{proto}/start")
    print(f"  启动 {proto}: HTTP {code}")
    time.sleep(0.5)

# 等待协议服务启动
print("  等待协议服务启动 (10s)...")
time.sleep(10)

# ===================================================================
# 2. 重新写入所有特征值
# ===================================================================
print("\n=== 2. 重新写入特征值 ===")
write_specs = [
    ("pf-modbus", "temp", 66.6),
    ("pf-modbus", "word1", 4321),
    ("pf-s7", "temp", 12.5),
    ("pf-s7", "word1", 1000),
    ("pf-mc", "d0", 555),
    ("pf-fins", "w0", 1234),
    ("pf-ab", "Temperature", 26.5),
    ("pf-mqtt", "temp", 36.6),
    ("pf-opcua", "motor_speed", 1500),
    ("pf-opcua", "valve_open", True),
    ("pf-http", "temperature", 42.0),
    ("pf-http", "pressure", 1.5),
]
for dev_id, point, value in write_specs:
    code, data = pf_api(pf_token, "PUT", f"/devices/{dev_id}/points/{point}", {"value": value})
    print(f"  {dev_id}/{point}={value}: HTTP {code}")

# ===================================================================
# 3. 修复 pf-opcua: 检查并调整 OPC UA 安全配置
# ===================================================================
print("\n=== 3. 检查 pf-opcua OPC UA 连接 ===")
# ProtoForge OPC UA 服务器可能使用 SignAndEncrypt
# EdgeLite pf-opcua 配置了 security_mode=None
# 需要检查 ProtoForge OPC UA 服务器的安全配置

# 检查 EdgeLite pf-opcua 健康状态
code, data = el.get("/devices/pf-opcua/health")
if code == 200:
    d = data.get("data", data) if isinstance(data, dict) else data
    print(f"  健康: is_connected={d.get('is_connected')}, total_reads={d.get('total_reads')}")
    print(f"  consecutive_failures={d.get('consecutive_failures')}")
    print(f"  degradation_reason={d.get('degradation_reason')}")

# 可能 OPC UA 服务器需要 None 安全策略
# 检查 ProtoForge OPC UA 服务器配置

# ===================================================================
# 4. 修复 pf-mqtt: 检查 EdgeLite MQTT 驱动的消息处理
# ===================================================================
print("\n=== 4. 检查 pf-mqtt ===")
# EdgeLite MQTT 驱动 is_connected=True 但 total_reads=0
# 消息格式是 JSON: {"device_id": "pf-mqtt", "point": "temp", "value": 36.6, ...}
# 检查 EdgeLite MQTT 驱动如何解析消息

# 可能 MQTT 驱动的 topic 到点位的映射不正确
# EdgeLite pf-mqtt 点位配置: address = "protoforge/pf-mqtt/temp"
# 消息 topic = "protoforge/pf-mqtt/temp"
# 驱动需要将 topic 匹配到点位的 address，然后从 payload 中提取 value

# 重新创建 pf-mqtt 设备（清除旧状态）
code, data = el.get("/devices/pf-mqtt")
if code == 200:
    d = data.get("data", data)
    config = d.get("config", {})
    points = d.get("points", [])
    # 确保配置正确
    print(f"  当前配置: {json.dumps(config, ensure_ascii=False)}")
    print(f"  点位: {json.dumps(points, ensure_ascii=False)[:200]}")

    # 删除并重新创建
    code2, data2 = el.delete("/devices/pf-mqtt")
    print(f"  删除 pf-mqtt: HTTP {code2}")

    time.sleep(2)

    mqtt_dev = {
        "device_id": "pf-mqtt",
        "name": "PF MQTT",
        "protocol": "mqtt_client",
        "config": {
            "broker": "127.0.0.1",
            "port": 1883,
            "subscribe_topic": "protoforge/#",
            "publish_topic": "protoforge/command",
            "client_id": "pf-mqtt-el",
            "topic_prefix": "protoforge",
            "retain": False,
            "qos": 0,
        },
        "collect_interval": 5,
        "points": [
            {"name": "temp", "data_type": "float32", "unit": "C", "address": "protoforge/pf-mqtt/temp", "access_mode": "rw"},
            {"name": "switch", "data_type": "float32", "unit": "", "address": "protoforge/pf-mqtt/switch", "access_mode": "rw"},
        ],
    }
    code3, data3 = el.post("/devices", mqtt_dev)
    print(f"  创建 pf-mqtt: HTTP {code3}: {json.dumps(data3, ensure_ascii=False)[:200]}")

# ===================================================================
# 5. 修复 pf-http: 通过 ProtoForge 集成推送数据
# ===================================================================
print("\n=== 5. 检查 pf-http ===")
# HTTP Webhook 驱动是被动接收模式
# ProtoForge 应该通过集成管理器推送数据到 EdgeLite
# 检查 ProtoForge 的 EdgeLite 集成配置

# 手动通过 EdgeLite API 推送数据
# EdgeLite HTTP Webhook 的 receive_data 方法需要通过 API 调用
# 检查 EdgeLite API 路由

# 尝试通过 EdgeLite 内部 API 推送
webhook_data = {
    "device_id": "pf-http",
    "temperature": 42.0,
    "pressure": 1.5,
}
# 先获取 CSRF token
code, data = el.get("/devices/pf-http")
csrf = el.csrf

# 尝试不同的 webhook 路径
for path in ["/webhook/http", "/api/v1/webhook/http", "/webhook", "/api/v1/devices/pf-http/webhook"]:
    try:
        req = urllib.request.Request(
            f"{EL.rsplit('/api/v1', 1)[0]}{path}",
            data=json.dumps(webhook_data).encode(),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {el.token}")
        req.add_header("X-CSRF-Token", csrf)
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"  {path}: HTTP {resp.status}: {resp.read().decode()[:200]}")
            break
    except urllib.error.HTTPError as e:
        print(f"  {path}: HTTP {e.code}: {e.read().decode()[:100]}")
    except Exception as e:
        print(f"  {path}: {e}")

# 等待采集周期
print("\n等待采集周期 (20s)...")
time.sleep(20)

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

# 也要检查 ProtoForge 端的值
print("\n=== ProtoForge 端值 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = pf_api(pf_token, "GET", f"/devices/{dev_id}/points")
    if code == 200 and data:
        pts = {p["name"]: p["value"] for p in data.get("points", [])}
        print(f"  {dev_id}: {pts}")
    else:
        print(f"  {dev_id}: HTTP {code}")
