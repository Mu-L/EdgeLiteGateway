#!/usr/bin/env python3
"""启动 ProtoForge MQTT 协议并写入特征值。"""
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
        with urllib.request.urlopen(req, data=data, timeout=20) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:500]}

token = pf_login()

# 启动 MQTT 协议
print("=== 启动 ProtoForge MQTT 协议 ===")
code, data = pf_api(token, "POST", "/protocols/mqtt/start")
print(f"  启动 MQTT: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:300] if data else ''}")

time.sleep(5)

# 写入特征值
print("\n=== 写入 pf-mqtt/temp=36.6 ===")
code, data = pf_api(token, "PUT", "/devices/pf-mqtt/points/temp", {"value": 36.6})
print(f"  HTTP {code}")

# 等待 MQTT 发布
print("\n等待 MQTT 发布 (10s)...")
time.sleep(10)

# 检查协议状态
code, data = pf_api(token, "GET", "/protocols")
if code == 200:
    protocols = data.get("protocols", data) if isinstance(data, dict) else data
    if isinstance(protocols, list):
        for p in protocols:
            name = p.get("name", p.get("protocol", ""))
            status = p.get("status", "")
            if name == "mqtt":
                print(f"  MQTT 状态: {status}")
