#!/usr/bin/env python3
"""快速诊断 ProtoForge 和 EdgeLite 的设备/点列表状态。"""
import json
import os
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
            return e.code, {"raw": raw[:300]}


pf_token = login(PF, PF_USER, PF_PASS)
el_token = login(EL, EL_USER, EL_PASS)
print("=== ProtoForge 设备列表 ===")
code, data = api(PF, pf_token, "GET", "/devices")
if code == 200 and data:
    for d in data.get("devices", []):
        print(f"  {d.get('id')}: protocol={d.get('protocol')} status={d.get('status')} points={len(d.get('points',[]))}")
        for p in d.get("points", []):
            print(f"    - {p.get('name')}: value={p.get('value')} addr={p.get('address')}")
else:
    print(f"  HTTP {code}: {data}")

print("\n=== ProtoForge 协议状态 ===")
code, data = api(PF, pf_token, "GET", "/protocols")
if code == 200 and data:
    for p in data.get("protocols", []):
        print(f"  {p.get('name')}: status={p.get('status')} port={p.get('port')}")
else:
    print(f"  HTTP {code}: {data}")

print("\n=== EdgeLite 设备列表 ===")
code, data = api(EL, el_token, "GET", "/devices")
if code == 200 and data:
    devices = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(devices, list):
        for d in devices:
            print(f"  {d.get('id')}: protocol={d.get('protocol')} status={d.get('status')}")
    elif isinstance(devices, dict):
        for k, v in devices.items():
            print(f"  {k}: {v}")
else:
    print(f"  HTTP {code}: {data}")

# 检查每个 EdgeLite 设备的点位
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = api(EL, el_token, "GET", f"/devices/{dev_id}/points")
    if code == 200 and data:
        points = data.get("data", data) if isinstance(data, dict) else data
        print(f"\n=== EdgeLite {dev_id} 点位 ===")
        if isinstance(points, dict):
            for name, info in points.items():
                if isinstance(info, dict):
                    print(f"  {name}: value={info.get('value')} addr={info.get('address','')}")
                else:
                    print(f"  {name}: {info}")
        elif isinstance(points, list):
            for p in points:
                print(f"  {p}")
    else:
        print(f"\n=== EdgeLite {dev_id}: HTTP {code} ===")

# 检查 ProtoForge 写入失败的设备
for dev_id in ["pf-mc", "pf-opcua", "pf-http"]:
    code, data = api(PF, pf_token, "GET", f"/devices/{dev_id}/points")
    if code == 200 and data:
        print(f"\n=== ProtoForge {dev_id} 点位 ===")
        for p in data.get("points", []):
            print(f"  {p.get('name')}: value={p.get('value')} addr={p.get('address')}")
    else:
        print(f"\n=== ProtoForge {dev_id}: HTTP {code} {data} ===")
