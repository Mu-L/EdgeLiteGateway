#!/usr/bin/env python3
"""通过 ProtoForge API 推送 pf-http 到 EdgeLite，触发 HTTP push loop。"""
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


def login(base, user, password):
    data = json.dumps({"username": user, "password": password}).encode()
    req = urllib.request.Request(f"{base}/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.load(resp)
    payload = body.get("data") if isinstance(body.get("data"), dict) else body
    return payload["access_token"]


def api(base, token, method, path, body=None, csrf=""):
    req = urllib.request.Request(f"{base}{path}", method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    if csrf:
        req.add_header("X-CSRF-Token", csrf)
    data = json.dumps(body).encode() if body else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as resp:
            raw = resp.read().decode()
            new_csrf = resp.headers.get("X-CSRF-Token", "")
            return resp.status, (json.loads(raw) if raw else None), new_csrf or csrf
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw), csrf
        except Exception:
            return e.code, {"raw": raw[:500]}, csrf


pf_token = login(PF, PF_USER, PF_PASS)
el_token = login(EL, EL_USER, EL_PASS)

# 1. 通过 ProtoForge 推送 pf-http 到 EdgeLite
print("=== 1. 通过 ProtoForge 推送 pf-http 到 EdgeLite ===")
code, data, _ = api(PF, pf_token, "POST", "/edgelite/push/pf-http")
print(f"  HTTP {code}: {json.dumps(data, ensure_ascii=False)[:500] if data else ''}")

# 2. 等待 HTTP push loop 推送数据
print("\n  等待 HTTP push loop (10s)...")
time.sleep(10)

# 3. 检查 EdgeLite pf-http 采集值
print("\n=== 2. 检查 EdgeLite pf-http 采集值 ===")
code, data, _ = api(EL, el_token, "GET", "/devices/pf-http/points")
if code == 200 and data:
    points = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(points, dict):
        vals = {k: v.get("value") if isinstance(v, dict) else v for k, v in points.items()}
        print(f"  pf-http: {vals}")

# 4. 同时直接通过 EdgeLite push API 推送一次数据（确保即时有值）
print("\n=== 3. 直接通过 EdgeLite push API 推送 ===")
push_payload = {
    "data": {
        "temperature": {"value": 42.0, "quality": "good", "timestamp": "2026-01-01T00:00:00Z"},
        "pressure": {"value": 1.5, "quality": "good", "timestamp": "2026-01-01T00:00:00Z"},
    }
}
code, data, _ = api(EL, el_token, "POST", "/devices/pf-http/push", push_payload)
print(f"  push: HTTP {code}")

# 5. 再次检查
time.sleep(3)
code, data, _ = api(EL, el_token, "GET", "/devices/pf-http/points")
if code == 200 and data:
    points = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(points, dict):
        vals = {k: v.get("value") if isinstance(v, dict) else v for k, v in points.items()}
        print(f"  pf-http: {vals}")

# 6. 验证所有设备
print("\n=== 4. 验证所有设备 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data, _ = api(EL, el_token, "GET", f"/devices/{dev_id}/points")
    if code == 200 and data:
        points = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(points, dict):
            vals = {k: v.get("value") if isinstance(v, dict) else v for k, v in points.items()}
            print(f"  {dev_id}: {vals}")
        else:
            print(f"  {dev_id}: {points}")
    else:
        print(f"  {dev_id}: HTTP {code}")
