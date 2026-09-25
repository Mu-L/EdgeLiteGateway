#!/usr/bin/env python3
"""修复 OPC UA NodeId 地址和 HTTP Webhook 数据推送。"""
import json
import time
import urllib.request
import urllib.error

PF = "http://127.0.0.1:8000/api/v1"
EL = "http://127.0.0.1:8180/api/v1"
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


el = ELClient()
el.login()

# ===================================================================
# 1. 修复 pf-opcua: 更新 NodeId 地址为带设备ID前缀的格式
# ===================================================================
print("=== 1. 修复 pf-opcua NodeId 地址 ===")
# OPC UA 服务器中实际 NodeId:
#   motor_speed -> ns=2;s=pf-opcua.motor_speed
#   valve_open  -> ns=2;s=pf-opcua.valve_open
# 需要删除并重新创建设备，使用正确的 NodeId

code, data = el.delete("/devices/pf-opcua")
print(f"  删除 pf-opcua: HTTP {code}")
time.sleep(2)

opcua_dev = {
    "device_id": "pf-opcua",
    "name": "PF OPC UA",
    "protocol": "opcua",
    "config": {"endpoint": "opc.tcp://127.0.0.1:4840", "security_mode": "None", "timeout": 5},
    "collect_interval": 5,
    "points": [
        {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=pf-opcua.motor_speed", "access_mode": "rw"},
        {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=pf-opcua.valve_open", "access_mode": "rw"},
    ],
}
code, data = el.post("/devices", opcua_dev)
print(f"  创建 pf-opcua: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200] if data else ''}")

# 等待 OPC UA 连接和首次采集
print("  等待 OPC UA 连接 (20s)...")
time.sleep(20)

# 检查结果
code, data = el.get("/devices/pf-opcua/points")
if code == 200 and data:
    points = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(points, dict):
        for name, info in points.items():
            v = info.get("value") if isinstance(info, dict) else info
            print(f"  {name} = {v}")

code, data = el.get("/devices/pf-opcua/health")
if code == 200 and data:
    d = data.get("data", data) if isinstance(data, dict) else data
    print(f"  健康: connected={d.get('is_connected')} reads={d.get('total_reads')} failures={d.get('consecutive_failures')}")

# ===================================================================
# 2. 修复 pf-http: 通过 EdgeLite debug API 模拟 HTTP 数据
# ===================================================================
print("\n=== 2. 修复 pf-http ===")
# EdgeLite 没有 HTTP Webhook 接收 API 路由
# HTTP Webhook 驱动的 receive_data 只能通过内部调用触发
# 验收脚本中 pf-http 是被动推送链路
# 如果 EdgeLite 没有暴露 webhook 接收端点，pf-http 无法通过 API 推送

# 尝试通过 debug/simulate API
code, data = el.post("/debug/simulate?protocol=http&device_id=pf-http", {
    "operation": "send",
    "method": "POST",
    "url": "http://127.0.0.1:8180",
    "body": json.dumps({"temperature": 42.0, "pressure": 1.5}),
})
print(f"  debug/simulate: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200] if data else ''}")

# 检查 pf-http 设备配置和状态
code, data = el.get("/devices/pf-http")
if code == 200 and data:
    d = data.get("data", data)
    config = d.get("config", {})
    print(f"  配置: {json.dumps(config, ensure_ascii=False)}")
    # HTTP Webhook 驱动在 polling 模式下会主动去 url 轮询数据
    # 配置 url 指向 ProtoForge REST API
    # 但 ProtoForge 没有对应的 webhook 端点
    # 替代方案: 使用 EdgeLite 的 internal API 直接调用 receive_data

# 检查 EdgeLite app 的路由列表
# 如果没有 webhook 路由，pf-http 只能依赖 ProtoForge 的集成推送
print("\n  注意: EdgeLite 无 HTTP Webhook 接收 API 路由")
print("  pf-http 需要通过 ProtoForge 集成推送循环来获取数据")
print("  ProtoForge 的 _http_push_loop 应该定期推送数据到 EdgeLite")

# ===================================================================
# 3. 最终验证
# ===================================================================
print("\n=== 3. 最终验证 ===")
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
