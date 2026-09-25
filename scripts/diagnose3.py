#!/usr/bin/env python3
"""诊断3：检查 ProtoForge S7/FINS/MC/MQTT 协议端口和设备绑定。"""
import json
import urllib.request
import urllib.error

PF = "http://127.0.0.1:8000/api/v1"
EL = "http://127.0.0.1:8180/api/v1"
PF_USER = "admin"
PF_PASS = "admin"
EL_USER = "admin"
EL_PASS = "EdgeLite@2026"


def login(base, user, password, token_field="access_token"):
    data = json.dumps({"username": user, "password": password}).encode()
    req = urllib.request.Request(f"{base}/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.load(resp)
    payload = body.get("data") if isinstance(body.get("data"), dict) else body
    return payload[token_field]


def api(base, token, method, path, body=None):
    req = urllib.request.Request(f"{base}{path}", method=method)
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


pf_token = login(PF, PF_USER, PF_PASS)
el_token = login(EL, EL_USER, EL_PASS)

# 1. 检查 ProtoForge 协议详情（含端口）
print("=== ProtoForge 协议详情 ===")
for proto in ["modbus_tcp", "s7", "fins", "mc", "mqtt", "opcua", "http"]:
    code, data = api(PF, pf_token, "GET", f"/protocols/{proto}")
    if code == 200 and data:
        p = data if isinstance(data, dict) else {}
        print(f"\n  {proto}:")
        print(f"    status={p.get('status')}")
        print(f"    port={p.get('port')}")
        config = p.get('config', {})
        if config:
            print(f"    config={json.dumps(config, ensure_ascii=False)}")
        # 打印完整数据
        for k, v in p.items():
            if k not in ('status', 'port', 'config', 'name'):
                print(f"    {k}={v}")
    else:
        print(f"\n  {proto}: HTTP {code}")

# 2. 检查 ProtoForge 中所有 S7 设备的配置
print("\n\n=== ProtoForge S7 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices?protocol=s7")
if code == 200 and data:
    for d in data.get("devices", []):
        print(f"  {d.get('id')}: status={d.get('status')}")
        for p in d.get("points", []):
            print(f"    point: {p.get('name')} = {p.get('value')}")

# 3. 检查 ProtoForge 中所有 FINS 设备
print("\n=== ProtoForge FINS 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices?protocol=fins")
if code == 200 and data:
    for d in data.get("devices", []):
        print(f"  {d.get('id')}: status={d.get('status')}")
        for p in d.get("points", []):
            print(f"    point: {p.get('name')} = {p.get('value')}")

# 4. 检查 ProtoForge 中所有 MC 设备
print("\n=== ProtoForge MC 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices?protocol=mc")
if code == 200 and data:
    for d in data.get("devices", []):
        print(f"  {d.get('id')}: status={d.get('status')}")
        for p in d.get("points", []):
            print(f"    point: {p.get('name')} = {p.get('value')}")

# 5. 检查 ProtoForge 中所有 MQTT 设备
print("\n=== ProtoForge MQTT 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices?protocol=mqtt")
if code == 200 and data:
    for d in data.get("devices", []):
        print(f"  {d.get('id')}: status={d.get('status')}")
        for p in d.get("points", []):
            print(f"    point: {p.get('name')} = {p.get('value')}")

# 6. 检查 ProtoForge 中所有 OPC UA 设备
print("\n=== ProtoForge OPC UA 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices?protocol=opcua")
if code == 200 and data:
    for d in data.get("devices", []):
        print(f"  {d.get('id')}: status={d.get('status')}")
        for p in d.get("points", []):
            print(f"    point: {p.get('name')} = {p.get('value')}")

# 7. 检查 ProtoForge 中所有 HTTP 设备
print("\n=== ProtoForge HTTP 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices?protocol=http")
if code == 200 and data:
    for d in data.get("devices", []):
        print(f"  {d.get('id')}: status={d.get('status')}")
        for p in d.get("points", []):
            print(f"    point: {p.get('name')} = {p.get('value')}")

# 8. 检查 ProtoForge 中所有 AB 设备
print("\n=== ProtoForge AB 设备 ===")
code, data = api(PF, pf_token, "GET", "/devices?protocol=ab")
if code == 200 and data:
    for d in data.get("devices", []):
        print(f"  {d.get('id')}: status={d.get('status')}")
        for p in d.get("points", []):
            print(f"    point: {p.get('name')} = {p.get('value')}")

# 9. 尝试写入 ProtoForge pf-fins/w0 并读取
print("\n=== 写入 ProtoForge pf-fins/w0 = 1234 ===")
code, data = api(PF, pf_token, "PUT", "/devices/pf-fins/points/w0", {"value": 1234})
print(f"  HTTP {code}: {json.dumps(data, ensure_ascii=False)}")

# 10. 尝试写入 ProtoForge pf-mqtt/temp = 36.6
print("\n=== 写入 ProtoForge pf-mqtt/temp = 36.6 ===")
code, data = api(PF, pf_token, "PUT", "/devices/pf-mqtt/points/temp", {"value": 36.6})
print(f"  HTTP {code}: {json.dumps(data, ensure_ascii=False)}")

# 11. 检查 EdgeLite 中 pf-s7 和 pf-fins 的健康
print("\n=== EdgeLite 设备健康 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-fins", "pf-mqtt", "pf-ab"]:
    code, data = api(EL, el_token, "GET", f"/devices/{dev_id}/health")
    if code == 200 and data:
        d = data.get("data", data) if isinstance(data, dict) else data
        print(f"  {dev_id}: {json.dumps(d, ensure_ascii=False)}")
    else:
        print(f"  {dev_id}: HTTP {code}")
