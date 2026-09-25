#!/usr/bin/env python3
"""检查 ProtoForge EdgeLite 集成状态并启动 HTTP push。"""
import json
import urllib.request
import urllib.error

PF = "http://127.0.0.1:8000/api/v1"
PF_USER = "admin"
PF_PASS = "admin"

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

token = pf_login()

# 检查集成状态
code, data = pf_api(token, "GET", "/edgelite/status")
print(f"EdgeLite 集成状态: HTTP {code}")
if code == 200 and data:
    d = data.get("data", data) if isinstance(data, dict) else data
    print(f"  enabled={d.get('enabled')} connected={d.get('connected')} url={d.get('url')}")
    print(f"  full: {json.dumps(d, ensure_ascii=False)[:500]}")

# 检查 pf-http 设备是否在 ProtoForge 中
code, data = pf_api(token, "GET", "/devices/pf-http")
if code == 200:
    d = data.get("device", data) if isinstance(data, dict) else data
    print(f"\npf-http 设备: status={d.get('status')}")
    for p in d.get("points", []):
        print(f"  {p.get('name')}: value={p.get('value')}")

# 尝试通过 edgelite/test 触发集成
code, data = pf_api(token, "POST", "/edgelite/test", {
    "url": "http://127.0.0.1:8180",
    "username": "admin",
    "password": "EdgeLite@2026",
})
print(f"\nEdgeLite 连接测试: HTTP {code}")
if data:
    print(f"  {json.dumps(data, ensure_ascii=False)[:300]}")

# 重新推送 pf-http 到 EdgeLite（触发 _start_http_push）
code, data = pf_api(token, "POST", "/edgelite/push", {"device_id": "pf-http"})
print(f"\n重新推送 pf-http: HTTP {code}")
if data:
    print(f"  {json.dumps(data, ensure_ascii=False)[:300]}")
