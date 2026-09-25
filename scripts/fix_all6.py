#!/usr/bin/env python3
"""修复脚本6：重启协议服务（带超时保护），重新写入特征值。"""
import json
import socket
import struct
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


def pf_api(token, method, path, body=None, timeout=10):
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
# 1. 重启 ProtoForge 协议服务（带超时保护）
# ===================================================================
print("=== 1. 重启 ProtoForge 协议服务 ===")
for proto in ["s7", "fins", "mc", "opcua", "http", "ab", "modbus_tcp"]:
    code, data = pf_api(pf_token, "POST", f"/protocols/{proto}/stop", timeout=5)
    print(f"  停止 {proto}: HTTP {code}")
    time.sleep(0.5)

# MQTT 需要特殊处理
code, data = pf_api(pf_token, "POST", "/protocols/mqtt/stop", timeout=5)
print(f"  停止 mqtt: HTTP {code}")
time.sleep(3)

for proto in ["modbus_tcp", "s7", "fins", "mc", "mqtt", "opcua", "http", "ab"]:
    code, data = pf_api(pf_token, "POST", f"/protocols/{proto}/start", timeout=10)
    print(f"  启动 {proto}: HTTP {code}")
    time.sleep(1)

print("  等待协议服务启动 (15s)...")
time.sleep(15)

# ===================================================================
# 2. 重新写入所有特征值
# ===================================================================
print("\n=== 2. 重新写入特征值 ===")
write_specs = [
    ("pf-modbus", "temp", 66.6),
    ("pf-modbus", "word1", 4321),
    ("pf-s7", "temp", 12.5),
    ("pf-s7", "word1", 1000),
    ("pf-mc", "d0", 555),
    ("pf-fins", "w0", 1234),
    ("pf-ab", "Temperature", 26.5),
    ("pf-mqtt", "temp", 36.6),
    ("pf-opcua", "motor_speed", 1500),
    ("pf-opcua", "valve_open", True),
    ("pf-http", "temperature", 42.0),
    ("pf-http", "pressure", 1.5),
]
for dev_id, point, value in write_specs:
    code, data = pf_api(pf_token, "PUT", f"/devices/{dev_id}/points/{point}", {"value": value})
    print(f"  {dev_id}/{point}={value}: HTTP {code}")

# 等待采集周期
print("\n等待采集周期 (20s)...")
time.sleep(20)

# ===================================================================
# 3. 验证 FINS 直读
# ===================================================================
print("\n=== 3. FINS 直读验证 ===")
def fins_read(addr_code, offset, port=9600):
    def recv_exact(s, n):
        buf = b""
        while len(buf) < n:
            c = s.recv(n - len(buf))
            if not c:
                raise ConnectionError("closed")
            buf += c
        return buf
    def recv_frame(s):
        h = recv_exact(s, 8)
        return recv_exact(s, struct.unpack(">I", h[4:8])[0])
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    try:
        init = struct.pack(">I", 0) + struct.pack(">I", 0) + struct.pack(">I", 0)
        s.sendall(b"FINS" + struct.pack(">I", len(init)) + init)
        recv_frame(s)
        fins_hdr = bytes([0x80, 0, 2, 0, 1, 0, 0, 0, 0, 1])
        data = bytes([addr_code]) + struct.pack(">H", offset) + bytes([0]) + struct.pack(">H", 1)
        body = struct.pack(">I", 2) + struct.pack(">I", 0) + fins_hdr + bytes([0x01, 0x01]) + data
        s.sendall(b"FINS" + struct.pack(">I", len(body)) + body)
        r = recv_frame(s)
        if len(r) >= 24:
            return int.from_bytes(r[22:24], "big")
        return None
    finally:
        s.close()

try:
    d0 = fins_read(0x82, 0)
    print(f"  FINS D0 (DM区) = {d0}")
except Exception as e:
    print(f"  FINS D0 读取失败: {e}")

# ===================================================================
# 4. 验证 S7 直读
# ===================================================================
print("\n=== 4. S7 直读验证 ===")
try:
    import snap7
    plc = snap7.client.Client()
    plc.connect("127.0.0.1", 0, 1, 102)
    try:
        data = plc.db_read(1, 0, 4)
        fval = struct.unpack(">f", data)[0]
        print(f"  snap7 DB1.D0 (float32) = {fval}")
        data2 = plc.db_read(1, 4, 2)
        ival = int.from_bytes(data2, "big", signed=True)
        print(f"  snap7 DB1.W4 (int16) = {ival}")
    finally:
        plc.disconnect()
except Exception as e:
    print(f"  snap7 读取失败: {e}")

# ===================================================================
# 5. 验证所有设备采集
# ===================================================================
print("\n=== 5. 验证所有设备采集 ===")
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

# 也检查 ProtoForge 端的值
print("\n=== ProtoForge 端值 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = pf_api(pf_token, "GET", f"/devices/{dev_id}/points")
    if code == 200 and data:
        pts = {p["name"]: p["value"] for p in data.get("points", [])}
        print(f"  {dev_id}: {pts}")
    else:
        print(f"  {dev_id}: HTTP {code}")
