#!/usr/bin/env python3
"""检查 EdgeLite 设备配置和采集值，以及 ProtoForge 设备的地址映射。"""
import json
import urllib.request
import urllib.error

PF = "http://127.0.0.1:8000/api/v1"
EL = "http://127.0.0.1:8180/api/v1"

def login(base, user, password):
    data = json.dumps({"username": user, "password": password, "no_revoke": True}).encode()
    req = urllib.request.Request(f"{base}/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.load(resp)
    payload = body.get("data") if isinstance(body.get("data"), dict) else body
    token = payload["access_token"]
    csrf = resp.headers.get("X-CSRF-Token", "")
    return token, csrf

def api(base, token, method, path, body=None, csrf=""):
    req = urllib.request.Request(f"{base}{path}", method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    if csrf:
        req.add_header("X-CSRF-Token", csrf)
    data = json.dumps(body).encode() if body else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=20) as resp:
            raw = resp.read().decode()
            new_csrf = resp.headers.get("X-CSRF-Token", "")
            return resp.status, (json.loads(raw) if raw else None), new_csrf or csrf
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw), csrf
        except Exception:
            return e.code, {"raw": raw[:500]}, csrf

pf_token, _ = login(PF, "admin", "admin")
el_token, el_csrf = login(EL, "admin", "EdgeLite@2026")

print("=== EdgeLite 设备配置 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data, el_csrf = api(EL, el_token, "GET", f"/devices/{dev_id}", csrf=el_csrf)
    if code == 200 and data:
        d = data.get("data", data) if isinstance(data, dict) else data
        config = d.get("config", {})
        points = d.get("points", [])
        print(f"\n{dev_id} (protocol={d.get('protocol')}):")
        print(f"  config: {json.dumps(config, ensure_ascii=False)}")
        for p in points:
            print(f"  point: {p.get('name')} addr={p.get('address')} type={p.get('data_type')}")
    else:
        print(f"\n{dev_id}: HTTP {code}")

print("\n=== ProtoForge 设备配置 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data, _ = api(PF, pf_token, "GET", f"/devices/{dev_id}")
    if code == 200:
        d = data.get("device", data) if isinstance(data, dict) else data
        points = d.get("points", [])
        print(f"\n{dev_id} (protocol={d.get('protocol')}):")
        for p in points:
            print(f"  point: {p.get('name')} addr={p.get('address')} value={p.get('value')}")
    else:
        print(f"\n{dev_id}: HTTP {code}")

print("\n=== EdgeLite 采集值 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data, el_csrf = api(EL, el_token, "GET", f"/devices/{dev_id}/points", csrf=el_csrf)
    if code == 200 and data:
        points = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(points, dict):
            vals = {k: v.get("value") if isinstance(v, dict) else v for k, v in points.items()}
            print(f"  {dev_id}: {vals}")
        else:
            print(f"  {dev_id}: {points}")
    else:
        print(f"  {dev_id}: HTTP {code}")
