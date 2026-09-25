#!/usr/bin/env python3
"""深入诊断：检查 ProtoForge 设备详情和 EdgeLite 设备配置。"""
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

# 1. 检查 ProtoForge 中 pf-fins 设备详情和写入
print("=== ProtoForge pf-fins 设备详情 ===")
code, data = api(PF, pf_token, "GET", "/devices/pf-fins")
if code == 200 and data:
    d = data.get("device", data)
    print(f"  id={d.get('id')} protocol={d.get('protocol')} status={d.get('status')}")
    print(f"  config={json.dumps(d.get('config',{}), indent=2)}")
    for p in d.get("points", []):
        print(f"  point: {p}")

# 尝试写入 pf-fins w0=1234
print("\n=== 尝试写入 ProtoForge pf-fins/w0 = 1234 ===")
code, data = api(PF, pf_token, "PUT", "/devices/pf-fins/points/w0", {"value": 1234})
print(f"  HTTP {code}: {json.dumps(data, indent=2)}")

# 2. 检查 ProtoForge 中 pf-s7 设备配置
print("\n=== ProtoForge pf-s7 设备详情 ===")
code, data = api(PF, pf_token, "GET", "/devices/pf-s7")
if code == 200 and data:
    d = data.get("device", data)
    print(f"  id={d.get('id')} protocol={d.get('protocol')} status={d.get('status')}")
    print(f"  config={json.dumps(d.get('config',{}), indent=2)}")
    for p in d.get("points", []):
        print(f"  point: {p}")

# 3. 检查 ProtoForge 中 pf-mqtt 设备配置
print("\n=== ProtoForge pf-mqtt 设备详情 ===")
code, data = api(PF, pf_token, "GET", "/devices/pf-mqtt")
if code == 200 and data:
    d = data.get("device", data)
    print(f"  id={d.get('id')} protocol={d.get('protocol')} status={d.get('status')}")
    print(f"  config={json.dumps(d.get('config',{}), indent=2)}")
    for p in d.get("points", []):
        print(f"  point: {p}")

# 4. 检查 EdgeLite 设备配置
print("\n=== EdgeLite 设备列表（含配置） ===")
code, data = api(EL, el_token, "GET", "/devices?include_config=true")
if code == 200 and data:
    devices = data.get("data", data)
    if isinstance(devices, list):
        for d in devices:
            print(f"  id={d.get('id')} name={d.get('name')} protocol={d.get('protocol')} status={d.get('status')}")
            conn = d.get("connection_config", {})
            if conn:
                print(f"    connection: {json.dumps(conn)}")
    elif isinstance(devices, dict):
        for k, v in devices.items():
            if isinstance(v, dict):
                print(f"  {k}: protocol={v.get('protocol')} conn={v.get('connection_config',{})}")
            else:
                print(f"  {k}: {v}")

# 5. 检查 EdgeLite 各设备的详细配置
for dev_id in ["pf-s7", "pf-fins", "pf-mqtt", "pf-mc", "pf-ab", "pf-opcua", "pf-http"]:
    code, data = api(EL, el_token, "GET", f"/devices/{dev_id}")
    if code == 200 and data:
        d = data.get("data", data)
        if isinstance(d, dict):
            print(f"\n=== EdgeLite {dev_id} 配置 ===")
            # 打印所有字段
            for k in sorted(d.keys()):
                v = d[k]
                if isinstance(v, (dict, list)):
                    print(f"  {k}: {json.dumps(v, ensure_ascii=False)}")
                else:
                    print(f"  {k}: {v}")
    else:
        print(f"\n=== EdgeLite {dev_id}: HTTP {code} ===")

# 6. 检查 ProtoForge 中 jt-s7 (可能冲突的设备)
print("\n=== ProtoForge jt-s7 设备详情 ===")
code, data = api(PF, pf_token, "GET", "/devices/jt-s7")
if code == 200 and data:
    d = data.get("device", data)
    print(f"  id={d.get('id')} protocol={d.get('protocol')} status={d.get('status')}")
    print(f"  config={json.dumps(d.get('config',{}), indent=2)}")

# 7. 检查 ProtoForge 协议端口配置
print("\n=== ProtoForge 协议详情 ===")
for proto in ["modbus_tcp", "s7", "fins", "mc", "mqtt", "opcua", "http", "ab"]:
    code, data = api(PF, pf_token, "GET", f"/protocols/{proto}")
    if code == 200 and data:
        p = data.get("protocol", data)
        print(f"  {proto}: status={p.get('status')} port={p.get('port')} config={json.dumps(p.get('config',{}))}")
