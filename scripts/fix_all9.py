#!/usr/bin/env python3
"""修复脚本9：通过 EdgeLite debug API 推送 HTTP Webhook 数据，修复 OPC UA NodeId。"""
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
# 1. 修复 pf-opcua: 检查 ProtoForge OPC UA 服务器的实际 NodeId
# ===================================================================
print("=== 1. 检查 OPC UA 服务器节点 ===")
# 用 asyncua 客户端浏览 OPC UA 服务器节点
try:
    from asyncua.sync import Client as SyncClient
    client = SyncClient(url="opc.tcp://127.0.0.1:4840")
    client.connect()
    try:
        # 获取 Objects 节点的子节点
        objects = client.nodes.objects
        children = objects.get_children()
        print(f"  Objects 子节点数: {len(children)}")
        for child in children[:20]:
            try:
                bname = child.read_browse_name()
                nid = child.nodeid
                print(f"    NodeId={nid} BrowseName={bname}")
            except:
                pass
    finally:
        client.disconnect()
except ImportError:
    # 尝试异步方式
    import asyncio

    async def browse_opcua():
        from asyncua import Client
        client = Client("opc.tcp://127.0.0.1:4840")
        await client.connect()
        try:
            objects = await client.get_objects_node()
            children = await objects.get_children()
            print(f"  Objects 子节点数: {len(children)}")
            for child in children[:20]:
                try:
                    bname = await child.read_browse_name()
                    nid = child.nodeid
                    print(f"    NodeId={nid} BrowseName={bname}")
                except:
                    pass
        finally:
            await client.disconnect()

    try:
        asyncio.run(browse_opcua())
    except Exception as e:
        print(f"  OPC UA 浏览失败: {e}")
except Exception as e:
    print(f"  OPC UA 浏览失败: {e}")

# ===================================================================
# 2. 通过 EdgeLite debug API 推送 HTTP Webhook 数据
# ===================================================================
print("\n=== 2. 推送 HTTP Webhook 数据 ===")
# 使用 debug simulate API
code, data = el.post("/debug/simulate?protocol=http&device_id=pf-http", {
    "method": "POST",
    "url": "http://127.0.0.1:8180",
    "body": json.dumps({"temperature": 42.0, "pressure": 1.5}),
})
print(f"  debug/simulate: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:300] if data else ''}")

# 也尝试直接调用 receive_data 通过内部 API
# 检查是否有 /api/v1/devices/{id}/webhook 端点
for path in [
    "/devices/pf-http/webhook",
    "/devices/pf-http/data",
    "/devices/pf-http/receive",
]:
    code, data = el.post(path, {"temperature": 42.0, "pressure": 1.5})
    print(f"  POST {path}: HTTP {code}: {json.dumps(data, ensure_ascii=False)[:200] if data else ''}")

# ===================================================================
# 3. 验证所有设备最终状态
# ===================================================================
print("\n=== 3. 最终验证 ===")
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

# ProtoForge 端值
print("\n=== ProtoForge 端值 ===")
for dev_id in ["pf-modbus", "pf-s7", "pf-mc", "pf-fins", "pf-ab", "pf-mqtt", "pf-opcua", "pf-http"]:
    code, data = pf_api(pf_token, "GET", f"/devices/{dev_id}/points")
    if code == 200 and data:
        pts = {p["name"]: p["value"] for p in data.get("points", [])}
        print(f"  {dev_id}: {pts}")
    else:
        print(f"  {dev_id}: HTTP {code}")
