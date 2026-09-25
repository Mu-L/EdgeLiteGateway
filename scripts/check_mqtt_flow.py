#!/usr/bin/env python3
"""检查 MQTT 消息流并写入特征值。"""
import json
import time
import urllib.request
import urllib.error
import threading

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

# 监听 MQTT 消息
import paho.mqtt.client as mqtt_lib

received = []

def on_message(client, userdata, msg):
    received.append({"topic": msg.topic, "payload": msg.payload.decode()[:200]})

client = mqtt_lib.Client()
client.on_message = on_message
client.connect("127.0.0.1", 1883, 60)
client.subscribe("protoforge/#")
client.loop_start()

print("MQTT 监听已启动，等待消息...")

# 写入特征值
token = pf_login()
code, data = pf_api(token, "PUT", "/devices/pf-mqtt/points/temp", {"value": 36.6})
print(f"写入 pf-mqtt/temp=36.6: HTTP {code}")

# 等待消息
time.sleep(10)
client.loop_stop()
client.disconnect()

print(f"\n收到 {len(received)} 条 MQTT 消息:")
for r in received:
    print(f"  topic={r['topic']} payload={r['payload']}")
