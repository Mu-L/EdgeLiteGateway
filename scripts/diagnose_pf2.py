#!/usr/bin/env python3
"""检查 ProtoForge 设备的实际点位地址分配。"""
import json
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

# 检查 ProtoForge 设备详情（完整 JSON）
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = pf_api(token, "GET", f"/devices/{dev_id}")
    if code == 200:
        d = data.get("device", data) if isinstance(data, dict) else data
        print(f"\n=== {dev_id} (protocol={d.get('protocol')}) ===")
        # 打印完整 points 配置
        points = d.get("points", [])
        for p in points:
            print(f"  point: {json.dumps(p, ensure_ascii=False)}")
        # 也打印 protocol_config
        pc = d.get("protocol_config", {})
        if pc:
            print(f"  protocol_config: {json.dumps(pc, ensure_ascii=False)}")
    else:
        print(f"\n{dev_id}: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:300] if data else ''}")

# 检查 Modbus 服务器监听的端口
print("\n=== 检查协议服务状态 ===")
code, data = pf_api(token, "GET", "/protocols")
if code == 200:
    protocols = data.get("protocols", data) if isinstance(data, dict) else data
    if isinstance(protocols, list):
        for p in protocols:
            name = p.get("name", p.get("protocol", ""))
            status = p.get("status", "")
            port = p.get("port", "")
            print(f"  {name}: status={status} port={port}")
    elif isinstance(protocols, dict):
        for name, info in protocols.items():
            print(f"  {name}: {json.dumps(info, ensure_ascii=False)[:200]}")
