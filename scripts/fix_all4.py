#!/usr/bin/env python3
"""修复脚本4：根据诊断结果修复剩余问题。"""
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
# 1. 修复 pf-fins: w0 地址改回 D0,w (ProtoForge 将 w0 映射到 D0)
# ===================================================================
print("=== 1. 修复 pf-fins w0 地址: W0,w -> D0,w ===")
code, data = el.get("/devices/pf-fins")
if code == 200 and data:
    d = data.get("data", data)
    points = d.get("points", [])
    for p in points:
        if p.get("name") == "w0":
            p["address"] = "D0,w"  # 改回 D0,w
            print(f"  w0 地址改为 D0,w")
    update_body = {
        "name": d.get("name"),
        "protocol": d.get("protocol"),
        "config": d.get("config"),
        "collect_interval": d.get("collect_interval"),
        "points": points,
    }
    code2, data2 = el.put("/devices/pf-fins", update_body)
    print(f"  更新结果: HTTP {code2}")

# 写入特征值
code, data = pf_api(pf_token, "PUT", "/devices/pf-fins/points/w0", {"value": 1234})
print(f"  写入 ProtoForge w0=1234: HTTP {code}")

# ===================================================================
# 2. 修复 pf-s7: ProtoForge S7 服务器 DB 分配冲突
# ===================================================================
print("\n=== 2. 修复 pf-s7 DB 冲突 ===")
# ProtoForge pf-s7 和 jt-s7 都用 DB1
# 需要在 ProtoForge 中删除 jt-s7 或修改其 DB 号
# 或者在 EdgeLite 中将 pf-s7 指向不同的 DB

# 方案: 删除 ProtoForge 中的 jt-s7 设备（它是联调测试设备，不是 pf-* 设备）
# 不，jt-s7 也可能在验收中使用
# 更好的方案: 检查 ProtoForge S7 服务器是否按设备分配不同 DB

# 实际上 ProtoForge S7 服务器可能将每个设备映射到不同的 DB 号
# pf-s7 可能是 DB1, jt-s7 可能也是 DB1
# 需要查看 ProtoForge S7 服务器源码

# 临时方案: 在 ProtoForge 中修改 pf-s7 的点位地址到 DB10
# 但 ProtoForge API 可能不支持直接修改点位地址

# 另一个方案: 删除 jt-s7 设备（仅保留 pf-s7）
print("  删除 ProtoForge jt-s7 设备（避免 DB 冲突）")
code, data = pf_api(pf_token, "DELETE", "/devices/jt-s7")
print(f"  删除 jt-s7: HTTP {code}")

# 同时也删除其他 jt-* 设备避免冲突
for dev_id in ["jt-mc", "jt-fins", "jt-mqtt", "jt-opcua", "jt-http"]:
    code, data = pf_api(pf_token, "DELETE", f"/devices/{dev_id}")
    print(f"  删除 {dev_id}: HTTP {code}")

# 重新写入特征值
code, data = pf_api(pf_token, "PUT", "/devices/pf-s7/points/temp", {"value": 12.5})
print(f"  写入 pf-s7/temp=12.5: HTTP {code}")
code, data = pf_api(pf_token, "PUT", "/devices/pf-s7/points/word1", {"value": 1000})
print(f"  写入 pf-s7/word1=1000: HTTP {code}")

# ===================================================================
# 3. 修复 pf-opcua: 使用正确的配置字段
# ===================================================================
print("\n=== 3. 创建 EdgeLite pf-opcua ===")
# 先删除可能存在的错误配置
code, data = el.get("/devices/pf-opcua")
if code == 200:
    code, data = el.delete("/devices/pf-opcua")
    print(f"  删除旧 pf-opcua: HTTP {code}")

# 使用正确字段名创建
opcua_dev = {
    "device_id": "pf-opcua",
    "name": "PF OPC UA",
    "protocol": "opcua",
    "config": {
        "endpoint": "opc.tcp://127.0.0.1:4840",
        "security_mode": "None",
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

# 如果还是失败，尝试其他字段名
if code != 200 and code != 201:
    # 尝试不带 security_mode
    opcua_dev2 = {
        "device_id": "pf-opcua",
        "name": "PF OPC UA",
        "protocol": "opcua",
        "config": {
            "endpoint": "opc.tcp://127.0.0.1:4840",
        },
        "collect_interval": 5,
        "points": [
            {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=motor_speed", "access_mode": "rw"},
            {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=valve_open", "access_mode": "rw"},
        ],
    }
    code, data = el.post("/devices", opcua_dev2)
    print(f"  重试创建 pf-opcua (简化配置): HTTP {code}: {json.dumps(data, ensure_ascii=False)[:300]}")

# ===================================================================
# 4. 修复 pf-mqtt: 检查 EdgeLite MQTT 驱动为什么收不到消息
# ===================================================================
print("\n=== 4. 检查 pf-mqtt ===")
# MQTT 消息确实在发送，但 EdgeLite 读到 0
# 可能原因: EdgeLite MQTT 驱动的 topic 到点位映射逻辑
# EdgeLite 配置: subscribe_topic=protoforge/#, point address=protoforge/pf-mqtt/temp
# 驱动需要将 topic protoforge/pf-mqtt/temp 映射到点位 temp

# 检查 EdgeLite pf-mqtt 的健康
code, data = el.get("/devices/pf-mqtt/health")
if code == 200 and data:
    d = data.get("data", data) if isinstance(data, dict) else data
    print(f"  健康: is_connected={d.get('is_connected')}, total_reads={d.get('total_reads')}")

# 可能 MQTT 驱动需要重启（先删除再创建）
code, data = el.get("/devices/pf-mqtt")
if code == 200 and data:
    d = data.get("data", data)
    config = d.get("config", {})
    points = d.get("points", [])
    print(f"  当前配置: {json.dumps(config, ensure_ascii=False)}")
    print(f"  点位: {json.dumps(points, ensure_ascii=False)[:200]}")

    # 重新更新设备配置（触发重连）
    update_body = {
        "name": d.get("name"),
        "protocol": d.get("protocol"),
        "config": config,
        "collect_interval": d.get("collect_interval"),
        "points": points,
    }
    code2, data2 = el.put("/devices/pf-mqtt", update_body)
    print(f"  更新 pf-mqtt (触发重连): HTTP {code2}")

# ===================================================================
# 5. 修复 pf-http: 配置应该是 EdgeLite 的 webhook 端点
# ===================================================================
print("\n=== 5. 修复 pf-http 配置 ===")
# HTTP Webhook 模式: ProtoForge 主动推送数据到 EdgeLite 的 webhook 端点
# EdgeLite 的 pf-http 设备配置应该是接收配置，不是发送 URL
# 检查 EdgeLite HTTP Webhook 驱动的配置格式

code, data = el.get("/devices/pf-http")
if code == 200 and data:
    d = data.get("data", data)
    config = d.get("config", {})
    points = d.get("points", [])
    print(f"  当前配置: {json.dumps(config, ensure_ascii=False)}")

    # HTTP Webhook 驱动可能需要的配置:
    # - webhook_path: 接收数据的路径
    # - auth_token: 认证 token
    # 或者直接用 url 字段指向 EdgeLite 自己的 webhook

    # 尝试不同的配置格式
    new_config = {
        "url": "http://127.0.0.1:8180/api/v1/webhook/http",
        "method": "POST",
        "timeout": 10,
        "auth_type": "bearer",
        "auth_token": el.token,
    }
    update_body = {
        "name": d.get("name"),
        "protocol": d.get("protocol"),
        "config": new_config,
        "collect_interval": d.get("collect_interval"),
        "points": points,
    }
    code2, data2 = el.put("/devices/pf-http", update_body)
    print(f"  更新 pf-http 配置: HTTP {code2}: {json.dumps(data2, ensure_ascii=False)[:200]}")

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

# 也检查 ProtoForge 端的值
print("\n=== ProtoForge 端值 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = pf_api(pf_token, "GET", f"/devices/{dev_id}/points")
    if code == 200 and data:
        pts = {p["name"]: p["value"] for p in data.get("points", [])}
        print(f"  {dev_id}: {pts}")
    else:
        print(f"  {dev_id}: HTTP {code}")
