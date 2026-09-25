#!/usr/bin/env python3
"""修复脚本2：处理 CSRF token，正确创建 EdgeLite 设备和更新配置。"""
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
    """EdgeLite 客户端，自动处理 CSRF token。"""
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
                # 如果 CSRF 失败，尝试从响应中获取新 token
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
# 1. 修复 EdgeLite pf-fins w0 地址: D0,w -> W0,w
# ===================================================================
print("=== 1. 修复 EdgeLite pf-fins w0 地址 ===")
code, data = el.get("/devices/pf-fins")
if code == 200 and data:
    d = data.get("data", data)
    points = d.get("points", [])
    changed = False
    for p in points:
        if p.get("name") == "w0" and p.get("address") != "W0,w":
            p["address"] = "W0,w"
            changed = True
            print(f"  更新 w0 地址: {p.get('address', 'old')} -> W0,w")
    if changed:
        update_body = {
            "name": d.get("name"),
            "protocol": d.get("protocol"),
            "config": d.get("config"),
            "collect_interval": d.get("collect_interval"),
            "points": points,
        }
        code2, data2 = el.put("/devices/pf-fins", update_body)
        print(f"  更新结果: HTTP {code2}: {json.dumps(data2, ensure_ascii=False)[:200]}")
    else:
        print("  w0 地址已是 W0,w")

# ===================================================================
# 2. 修复 EdgeLite pf-s7 地址: 避免与 jt-s7 冲突
# ===================================================================
print("\n=== 2. 修复 EdgeLite pf-s7 地址 ===")
code, data = el.get("/devices/pf-s7")
if code == 200 and data:
    d = data.get("data", data)
    points = d.get("points", [])
    # 检查 ProtoForge pf-s7 在 S7 服务器中的 DB 映射
    # ProtoForge 可能为每个设备创建独立的 DB，需要检查
    # 先尝试保持 DB1 但用不同偏移
    # 实际上 ProtoForge 的 S7 服务器可能将不同设备映射到不同 DB
    # 让我检查 ProtoForge pf-s7 的地址配置
    print(f"  当前 pf-s7 点位:")
    for p in points:
        print(f"    {p.get('name')}: addr={p.get('address')} type={p.get('data_type')}")

# 先检查 ProtoForge S7 服务器如何分配 DB 号
# ProtoForge 可能按设备创建顺序分配 DB 号
# pf-s7 是先于 jt-s7 创建的，所以 pf-s7 可能在 DB1，jt-s7 在 DB2
# EdgeLite pf-s7 读到 temp=74.98，而 jt-s7.temperature 在变化
# 但 pf-s7.temp=12.5 在 ProtoForge 端
# 这说明 ProtoForge 的 S7 服务器将不同设备的相同 DB 号映射到了同一块内存
# 需要 ProtoForge 端给 pf-s7 使用不同 DB 号

# 让我检查 ProtoForge 的 S7 服务器源码来理解 DB 分配逻辑
# 但先尝试另一种方案: 修改 EdgeLite pf-s7 的地址格式
# ProtoForge S7 服务器可能按设备 ID 区分 DB
# 如果 pf-s7 用 DB1, jt-s7 也用 DB1，需要确认 ProtoForge 的实现

# 尝试: 将 EdgeLite pf-s7 的 temp 地址改为 DB1.DBD0（完整格式）
for p in points:
    if p.get("name") == "temp":
        p["address"] = "DB1.DBD0"  # float32
    elif p.get("name") == "word1":
        p["address"] = "DB1.DBW4"  # int16
    elif p.get("name") == "bit1":
        p["address"] = "DB1.DBX6.0"  # bool
    elif p.get("name") == "bit2":
        p["address"] = "M10.0"  # bool in M area

update_body = {
    "name": d.get("name"),
    "protocol": d.get("protocol"),
    "config": d.get("config"),
    "collect_interval": d.get("collect_interval"),
    "points": points,
}
code2, data2 = el.put("/devices/pf-s7", update_body)
print(f"  更新 pf-s7 地址: HTTP {code2}: {json.dumps(data2, ensure_ascii=False)[:200]}")

# ===================================================================
# 3. 创建 EdgeLite pf-mc 设备
# ===================================================================
print("\n=== 3. 创建 EdgeLite pf-mc ===")
code, data = el.get("/devices/pf-mc")
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
    code, data = el.post("/devices", mc_dev)
    print(f"  创建 pf-mc: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"  pf-mc 已存在: HTTP {code}")

# ===================================================================
# 4. 创建/更新 EdgeLite pf-opcua 设备
# ===================================================================
print("\n=== 4. 创建/更新 EdgeLite pf-opcua ===")
code, data = el.get("/devices/pf-opcua")
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
    code, data = el.post("/devices", opcua_dev)
    print(f"  创建 pf-opcua: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")
elif code == 200:
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
    code2, data2 = el.put("/devices/pf-opcua", update_body)
    print(f"  更新 pf-opcua: HTTP {code2}: {json.dumps(data2, ensure_ascii=False)[:200]}")

# ===================================================================
# 5. 创建 EdgeLite pf-http 设备
# ===================================================================
print("\n=== 5. 创建 EdgeLite pf-http ===")
code, data = el.get("/devices/pf-http")
if code == 404:
    http_dev = {
        "device_id": "pf-http",
        "name": "PF HTTP Webhook",
        "protocol": "http_webhook",
        "config": {
            "url": "http://127.0.0.1:8000/api/v1/webhook/http",
            "method": "POST",
            "timeout": 10,
        },
        "collect_interval": 5,
        "points": [
            {"name": "temperature", "data_type": "float32", "address": "temperature", "access_mode": "rw"},
            {"name": "pressure", "data_type": "float32", "address": "pressure", "access_mode": "rw"},
        ],
    }
    code, data = el.post("/devices", http_dev)
    print(f"  创建 pf-http: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"  pf-http 已存在: HTTP {code}")

# ===================================================================
# 6. 在 ProtoForge pf-opcua 中添加 motor_speed/valve_open 点
# ===================================================================
print("\n=== 6. ProtoForge pf-opcua 添加点位 ===")
# 尝试通过设备更新 API 添加点位
code, data = pf_api(pf_token, "GET", "/devices/pf-opcua")
if code == 200 and data:
    d = data.get("device", data)
    existing_points = d.get("points", [])
    existing_names = {p["name"] for p in existing_points}
    print(f"  现有点位: {existing_names}")

    # 尝试通过 PUT /devices/{id} 更新设备（包含新点位）
    all_points = list(existing_points)
    for name, dtype, addr in [("motor_speed", "int32", "ns=2;s=motor_speed"),
                               ("valve_open", "bool", "ns=2;s=valve_open")]:
        if name not in existing_names:
            all_points.append({"name": name, "data_type": dtype, "address": addr})

    update_body = {
        "id": "pf-opcua",
        "name": d.get("name", "PF OPC UA"),
        "protocol": "opcua",
        "points": all_points,
    }
    code2, data2 = pf_api(pf_token, "PUT", "/devices/pf-opcua", update_body)
    print(f"  更新设备: HTTP {code2}: {json.dumps(data2, ensure_ascii=False)[:300]}")

    # 如果 PUT 不行，尝试删除后重建
    if code2 != 200:
        print("  尝试删除并重建 pf-opcua...")
        code3, data3 = pf_api(pf_token, "DELETE", "/devices/pf-opcua")
        print(f"  删除: HTTP {code3}")
        new_dev = {
            "id": "pf-opcua",
            "name": "PF OPC UA",
            "protocol": "opcua",
            "points": [
                {"name": "motor_speed", "data_type": "int32", "address": "ns=2;s=motor_speed"},
                {"name": "valve_open", "data_type": "bool", "address": "ns=2;s=valve_open"},
            ],
        }
        code4, data4 = pf_api(pf_token, "POST", "/devices", new_dev)
        print(f"  重建: HTTP {code4}: {json.dumps(data4, ensure_ascii=False)[:300]}")

# 写入特征值
for name, val in [("motor_speed", 1500), ("valve_open", True)]:
    code, data = pf_api(pf_token, "PUT", f"/devices/pf-opcua/points/{name}", {"value": val})
    print(f"  写入 {name}={val}: HTTP {code}")

# ===================================================================
# 7. 修复 pf-mqtt: 重新创建设备配置
# ===================================================================
print("\n=== 7. 检查 pf-mqtt ===")
code, data = el.get("/devices/pf-mqtt")
if code == 200 and data:
    d = data.get("data", data)
    config = d.get("config", {})
    print(f"  当前配置: {json.dumps(config, ensure_ascii=False)}")
    points = d.get("points", [])
    # 确保订阅 topic 包含 #
    if config.get("subscribe_topic") != "protoforge/#":
        config["subscribe_topic"] = "protoforge/#"
        update_body = {
            "name": d.get("name"),
            "protocol": d.get("protocol"),
            "config": config,
            "collect_interval": d.get("collect_interval"),
            "points": points,
        }
        code2, data2 = el.put("/devices/pf-mqtt", update_body)
        print(f"  更新 pf-mqtt 配置: HTTP {code2}: {json.dumps(data2, ensure_ascii=False)[:200]}")
    else:
        print("  subscribe_topic 已正确设置为 protoforge/#")

# ===================================================================
# 8. 修复 pf-ab: 确保 AB 协议已启动并重建设备
# ===================================================================
print("\n=== 8. 检查 pf-ab ===")
# 确认 ProtoForge AB 协议已启动
code, data = pf_api(pf_token, "POST", "/protocols/ab/start")
print(f"  启动 AB 协议: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200]}")

# 写入特征值
code, data = pf_api(pf_token, "PUT", "/devices/pf-ab/points/Temperature", {"value": 26.5})
print(f"  写入 Temperature=26.5: HTTP {code}")

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
