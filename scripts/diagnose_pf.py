#!/usr/bin/env python3
"""检查 ProtoForge 设备的点位配置。"""
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

for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = pf_api(token, "GET", f"/devices/{dev_id}")
    if code == 200:
        d = data.get("device", data) if isinstance(data, dict) else data
        points = d.get("points", [])
        pt_names = [p.get("name") for p in points]
        print(f"{dev_id} (protocol={d.get('protocol')}, status={d.get('status')}):")
        for p in points:
            print(f"  {p.get('name')}: value={p.get('value')} address={p.get('address')} type={p.get('data_type')}")
    else:
        print(f"{dev_id}: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200] if data else ''}")
