#!/usr/bin/env python3
"""诊断4：深入检查 pf-fins、pf-s7、pf-mqtt 的根本原因。"""
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


pf_token = pf_login()
el = ELClient()
el.login()

# ===================================================================
# 1. 深入检查 pf-fins: ProtoForge 写入 vs FINS 服务器实际值
# ===================================================================
print("=== 1. pf-fins 深入诊断 ===")

# ProtoForge 端 w0=1234
code, data = pf_api(pf_token, "GET", "/devices/pf-fins/points")
pf_w0 = None
if code == 200:
    for p in data.get("points", []):
        if p["name"] == "w0":
            pf_w0 = p["value"]
            print(f"  ProtoForge pf-fins/w0 = {pf_w0}")

# FINS 直读 D0
def fins_read(addr_code, offset, port=9600):
    """直读 FINS 字地址"""
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

# 读 D0 (DM区, 0x82)
try:
    d0 = fins_read(0x82, 0)
    print(f"  FINS D0 直读 = {d0}")
except Exception as e:
    print(f"  FINS D0 直读失败: {e}")

# 读 W0 (WR区, 0xB1)
try:
    w0 = fins_read(0xB1, 0)
    print(f"  FINS W0 直读 = {w0}")
except Exception as e:
    print(f"  FINS W0 直读失败: {e}")

# 读 D0 使用 EdgeLite 非标准区码 0xB4
try:
    w0_edgelite = fins_read(0xB4, 0)
    print(f"  FINS W0(EdgeLite 0xB4) 直读 = {w0_edgelite}")
except Exception as e:
    print(f"  FINS W0(0xB4) 直读失败: {e}")

# EdgeLite 端 w0 配置
code, data = el.get("/devices/pf-fins")
if code == 200:
    d = data.get("data", data)
    for p in d.get("points", []):
        if p.get("name") == "w0":
            print(f"  EdgeLite w0 地址: {p.get('address')}")

# EdgeLite 端 w0 值
code, data = el.get("/devices/pf-fins/points")
if code == 200:
    points = data.get("data", data)
    if isinstance(points, dict):
        w0_info = points.get("w0", {})
        print(f"  EdgeLite w0 值: {w0_info.get('value') if isinstance(w0_info, dict) else w0_info}")

# ===================================================================
# 2. 深入检查 pf-s7: 删除 jt-s7 后 S7 服务器状态
# ===================================================================
print("\n=== 2. pf-s7 深入诊断 ===")
# 使用 snap7 直读 DB1.D0 (float32)
try:
    import snap7
    plc = snap7.client.Client()
    plc.connect("127.0.0.1", 0, 1, 102)
    try:
        # 读 DB1.D0 (4 bytes = float32)
        data = plc.db_read(1, 0, 4)
        import struct as s2
        fval = s2.unpack(">f", data)[0]
        print(f"  snap7 DB1.D0 (float32) = {fval}")

        # 读 DB1.W4 (2 bytes = int16)
        data2 = plc.db_read(1, 4, 2)
        ival = int.from_bytes(data2, "big", signed=True)
        print(f"  snap7 DB1.W4 (int16) = {ival}")

        # 也读 DB1.DBW4
        data3 = plc.db_read(1, 4, 2)
        ival2 = int.from_bytes(data3, "big", signed=True)
        print(f"  snap7 DB1.DBW4 (int16) = {ival2}")
    finally:
        plc.disconnect()
except Exception as e:
    print(f"  snap7 读取失败: {e}")

# EdgeLite pf-s7 值
code, data = el.get("/devices/pf-s7/points")
if code == 200:
    points = data.get("data", data)
    if isinstance(points, dict):
        for name, info in points.items():
            v = info.get("value") if isinstance(info, dict) else info
            print(f"  EdgeLite {name} = {v}")

# ===================================================================
# 3. 深入检查 pf-mqtt: 为什么 EdgeLite 收不到 MQTT 消息
# ===================================================================
print("\n=== 3. pf-mqtt 深入诊断 ===")
# 检查 EdgeLite MQTT 驱动日志
# 尝试手动发送 MQTT 消息
try:
    import paho.mqtt.client as mqtt_lib
    import paho.mqtt.publish as publish

    # 发送一条测试消息
    payload = json.dumps({
        "device_id": "pf-mqtt",
        "point": "temp",
        "value": 36.6,
        "timestamp": time.time(),
        "unit": "C"
    })
    publish.single("protoforge/pf-mqtt/temp", payload, hostname="127.0.0.1", port=1883)
    print(f"  已发送 MQTT 消息: protoforge/pf-mqtt/temp = 36.6")

    time.sleep(3)

    # 检查 EdgeLite 是否收到
    code, data = el.get("/devices/pf-mqtt/points")
    if code == 200:
        points = data.get("data", data)
        if isinstance(points, dict):
            temp_info = points.get("temp", {})
            temp_val = temp_info.get("value") if isinstance(temp_info, dict) else temp_info
            print(f"  EdgeLite pf-mqtt/temp = {temp_val}")
except ImportError:
    print("  paho-mqtt 未安装")
except Exception as e:
    print(f"  MQTT 测试失败: {e}")

# 检查 EdgeLite pf-mqtt 健康
code, data = el.get("/devices/pf-mqtt/health")
if code == 200:
    d = data.get("data", data) if isinstance(data, dict) else data
    print(f"  健康: is_connected={d.get('is_connected')}, total_reads={d.get('total_reads')}")
    print(f"  完整健康: {json.dumps(d, ensure_ascii=False)[:300]}")

# ===================================================================
# 4. 检查 pf-opcua 状态
# ===================================================================
print("\n=== 4. pf-opcua 状态 ===")
code, data = el.get("/devices/pf-opcua/health")
if code == 200:
    d = data.get("data", data) if isinstance(data, dict) else data
    print(f"  健康: is_connected={d.get('is_connected')}, total_reads={d.get('total_reads')}")
else:
    print(f"  HTTP {code}")

code, data = el.get("/devices/pf-opcua/points")
if code == 200:
    points = data.get("data", data)
    if isinstance(points, dict):
        for name, info in points.items():
            v = info.get("value") if isinstance(info, dict) else info
            print(f"  {name} = {v}")

# ===================================================================
# 5. 检查 pf-http 状态
# ===================================================================
print("\n=== 5. pf-http 状态 ===")
code, data = el.get("/devices/pf-http/health")
if code == 200:
    d = data.get("data", data) if isinstance(data, dict) else data
    print(f"  健康: is_connected={d.get('is_connected')}, total_reads={d.get('total_reads')}")
else:
    print(f"  HTTP {code}")

# 检查 HTTP Webhook 接收端点
# EdgeLite HTTP Webhook 应该有一个接收端点
# 检查 EdgeLite API 中是否有 webhook 接收路由
print("\n  尝试向 EdgeLite 推送 HTTP Webhook 数据...")
# 先获取 token
el_token = el.token
webhook_data = {
    "device_id": "pf-http",
    "temperature": 42.0,
    "pressure": 1.5,
}
try:
    req = urllib.request.Request(
        f"{EL}/webhook/http",
        data=json.dumps(webhook_data).encode(),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {el_token}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"  Webhook 推送: HTTP {resp.status}: {resp.read().decode()[:200]}")
except urllib.error.HTTPError as e:
    print(f"  Webhook 推送失败: HTTP {e.code}: {e.read().decode()[:200]}")
except Exception as e:
    print(f"  Webhook 推送异常: {e}")

# 等待后检查
time.sleep(3)
code, data = el.get("/devices/pf-http/points")
if code == 200:
    points = data.get("data", data)
    if isinstance(points, dict):
        for name, info in points.items():
            v = info.get("value") if isinstance(info, dict) else info
            print(f"  {name} = {v}")
