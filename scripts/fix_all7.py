#!/usr/bin/env python3
"""修复脚本7：重启 MQTT/OPC UA 协议，触发 EdgeLite 设备重连。"""
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


def pf_api(token, method, path, body=None, timeout=15):
    req = urllib.request.Request(f"{PF}{path}", method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:500]}
    except Exception as e:
        return 0, {"error": str(e)}


pf_token = pf_login()
el = ELClient()
el.login()

# ===================================================================
# 1. 重启 MQTT 和 OPC UA 协议（之前启动超时了）
# ===================================================================
print("=== 1. 重启 MQTT 和 OPC UA 协议 ===")
for proto in ["mqtt", "opcua"]:
    # 先检查状态
    code, data = pf_api(pf_token, "GET", f"/protocols/{proto}", timeout=10)
    if code == 200 and data:
        status = data.get("status", data.get("protocol", {}).get("status", ""))
        print(f"  {proto} 当前状态: {status}")

    # 启动
    code, data = pf_api(pf_token, "POST", f"/protocols/{proto}/start", timeout=30)
    print(f"  启动 {proto}: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200] if data else ''}")

time.sleep(10)

# ===================================================================
# 2. 触发 EdgeLite 设备重连（通过更新设备配置）
# ===================================================================
print("\n=== 2. 触发 EdgeLite 设备重连 ===")
for dev_id in ["pf-s7", "pf-fins", "pf-mqtt", "pf-opcua"]:
    code, data = el.get(f"/devices/{dev_id}")
    if code == 200 and data:
        d = data.get("data", data)
        # 重新 PUT 一次相同配置，触发驱动重连
        update_body = {
            "name": d.get("name"),
            "protocol": d.get("protocol"),
            "config": d.get("config"),
            "collect_interval": d.get("collect_interval"),
            "points": d.get("points", []),
        }
        code2, data2 = el.put(f"/devices/{dev_id}", update_body)
        print(f"  更新 {dev_id}: HTTP {code2}")

# ===================================================================
# 3. 重新写入特征值
# ===================================================================
print("\n=== 3. 重新写入特征值 ===")
for dev_id, point, value in [
    ("pf-s7", "temp", 12.5), ("pf-s7", "word1", 1000),
    ("pf-fins", "w0", 1234),
    ("pf-mqtt", "temp", 36.6),
    ("pf-opcua", "motor_speed", 1500), ("pf-opcua", "valve_open", True),
]:
    code, data = pf_api(pf_token, "PUT", f"/devices/{dev_id}/points/{point}", {"value": value})
    print(f"  {dev_id}/{point}={value}: HTTP {code}")

# 等待采集周期
print("\n等待采集周期 (30s)...")
time.sleep(30)

# ===================================================================
# 4. 验证所有设备采集
# ===================================================================
print("\n=== 4. 验证所有设备采集 ===")
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

# 检查健康状态
print("\n=== 健康状态 ===")
for dev_id in ["pf-s7", "pf-fins", "pf-mqtt", "pf-opcua"]:
    code, data = el.get(f"/devices/{dev_id}/health")
    if code == 200 and data:
        d = data.get("data", data) if isinstance(data, dict) else data
        print(f"  {dev_id}: connected={d.get('is_connected')} total_reads={d.get('total_reads')} failures={d.get('consecutive_failures')} reason={d.get('degradation_reason')}")
    else:
        print(f"  {dev_id}: HTTP {code}")
