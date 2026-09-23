#!/usr/bin/env python3
"""ProtoForge <-> EdgeLite 联调验收脚本（生产级可重复执行）。

对由 ProtoForge 模拟的工业设备矩阵执行三阶段验收：

  A. 采集一致性：向 ProtoForge 源端写入特征值 -> 等待采集周期 -> 从 EdgeLite
     读取并比对（验证 设备->网关 方向的协议解析与数据链路）。
  B. 下写链路：通过 EdgeLite API 下写 -> 从 ProtoForge 线上内存读回比对
     （验证 网关->设备 方向的地址映射与写帧）。
  C. 故障注入：停止 ProtoForge 协议/设备 -> 观察 EdgeLite 状态降级 ->
     恢复后观察重新上线（验证故障感知与自愈）。

用法（凭据一律走环境变量，禁止硬编码）：
    set PF_URL=http://127.0.0.1:8000/api/v1
    set PF_USER=admin & set PF_PASS=admin
    set EL_URL=http://127.0.0.1:8180/api/v1
    set EL_USER=admin & set EL_PASS=<your-admin-password>
    python scripts/joint_acceptance.py [--skip-write] [--skip-fault] [--report out.json]

退出码：存在失败项时为 1，可作为 CI/验收门禁。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

PF = os.environ.get("PF_URL", "http://127.0.0.1:8000/api/v1")
EL = os.environ.get("EL_URL", "http://127.0.0.1:8180/api/v1")
PF_USER = os.environ.get("PF_USER", "admin")
PF_PASS = os.environ.get("PF_PASS", "admin")
EL_USER = os.environ.get("EL_USER", "admin")
EL_PASS = os.environ.get("EL_PASS", "")

# 联调设备矩阵：EdgeLite 设备ID -> (ProtoForge 设备ID, 协议, 采集用测点 -> 源端写入值,
#                                 下写用测点 -> EdgeLite 下写值, 线上读回器)
# 值选取避开 0（0 无法区分"采集失败"与"恰好为 0"）。
# 线上读回器（wire_reader）用独立第三方协议客户端直读设备内存，
# 避免 ProtoForge REST 点位注册表与线上内存不一致导致的假阳性/假阴性。
MATRIX: dict[str, dict] = {
    "pf-modbus": {
        "pf": "pf-modbus",
        "protocol": "modbus_tcp",
        "collect_points": {"temp": 66.6, "word1": 4321},
        # FIXED-JOINT: 写用例选保持寄存器点位（word1=HR102）。IR 是 Modbus 只读输入区，
        # 驱动对 IR 点位的写会映射到同号保持寄存器（兼容行为），不作为下写验收依据。
        "write_point": ("word1", 888),
        "wire_reader": ("modbus", 5020, 1, {"word1": ("hr", 102)}),
    },
    "pf-s7": {
        "pf": "pf-s7",
        "protocol": "siemens_s7",
        "collect_points": {"temp": 12.5, "word1": 1000},
        "write_point": ("word1", 888),
        "wire_reader": ("snap7", 102, {"word1": (1, 4)}),  # (db, byte)
    },
    "pf-mc": {
        "pf": "pf-mc",
        "protocol": "mitsubishi_mc",
        "collect_points": {"d0": 555},
        "write_point": ("d0", 999),
        "wire_reader": ("mc", 5000, {"d0": "D0"}),
    },
    "pf-fins": {
        "pf": "pf-fins",
        "protocol": "omron_fins",
        "collect_points": {"w0": 1234},
        "write_point": ("w0", 4321),
        "wire_reader": ("fins", 9600, {"w0": 0}),  # DM 字地址
    },
    "pf-ab": {
        "pf": "pf-ab",
        "protocol": "allen_bradley",
        "collect_points": {"Temperature": 26.5},
        "write_point": ("Setpoint", 50),
        "wire_reader": ("pylogix", 44818, {"Setpoint": "Setpoint"}),
    },
    "pf-mqtt": {
        "pf": "pf-mqtt",
        "protocol": "mqtt_client",
        "collect_points": {"temp": 36.6},
        "write_point": None,  # MQTT 为只读订阅链路
    },
}

COLLECT_WAIT_SECONDS = float(os.environ.get("JOINT_COLLECT_WAIT", "12"))
FAULT_WAIT_SECONDS = float(os.environ.get("JOINT_FAULT_WAIT", "20"))
RECOVER_WAIT_SECONDS = float(os.environ.get("JOINT_RECOVER_WAIT", "120"))


class Client:
    """极简 REST 客户端：自动登录、401 自动重登（并发登录控制下 token 可能被顶掉）。"""

    def __init__(self, base: str, user: str, password: str, token_field: str = "access_token"):
        self.base = base
        self.user = user
        self.password = password
        self.token_field = token_field
        self.token = ""
        self.csrf = ""

    def _login(self) -> None:
        data = json.dumps({"username": self.user, "password": self.password}).encode()
        req = urllib.request.Request(f"{self.base}/auth/login", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.load(resp)
        payload = body.get("data") if isinstance(body.get("data"), dict) else body
        self.token = payload[self.token_field]

    def request(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | None]:
        if not self.token:
            self._login()
        for attempt in (1, 2):
            req = urllib.request.Request(f"{self.base}{path}", method=method)
            req.add_header("Authorization", f"Bearer {self.token}")
            req.add_header("Content-Type", "application/json")
            if self.csrf:
                req.add_header("X-CSRF-Token", self.csrf)
            data = json.dumps(body).encode() if body is not None else None
            try:
                with urllib.request.urlopen(req, data=data, timeout=20) as resp:
                    raw = resp.read().decode()
                    self.csrf = resp.headers.get("X-CSRF-Token") or self.csrf
                    return resp.status, (json.loads(raw) if raw else None)
            except urllib.error.HTTPError as e:
                raw = e.read().decode()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    payload = {"raw": raw[:200]}
                if e.code == 401 and attempt == 1:
                    self._login()
                    continue
                return e.code, payload
        raise RuntimeError("unreachable")

    def get(self, path: str):
        return self.request("GET", path)

    def post(self, path: str, body: dict | None = None):
        return self.request("POST", path, body or {})

    def put(self, path: str, body: dict | None = None):
        return self.request("PUT", path, body or {})


def unwrap_el(payload: dict | list | None):
    """EdgeLite ApiResponse 解包：data 字段。"""
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def el_points(el: Client, device_id: str) -> dict:
    code, payload = el.get(f"/devices/{device_id}/points")
    if code != 200:
        return {}
    data = unwrap_el(payload) or {}
    out = {}
    for name, info in data.items():
        if isinstance(info, dict):
            out[name] = info.get("value")
        else:
            out[name] = info
    return out


def pf_points(pf: Client, device_id: str) -> dict:
    code, payload = pf.get(f"/devices/{device_id}/points")
    if code != 200:
        return {}
    data = payload.get("points", []) if isinstance(payload, dict) else []
    return {p.get("name"): p.get("value") for p in data}


def values_match(a, b, tol=1e-3) -> bool:
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return str(a) == str(b)


def wait_devices_online(el: Client, timeout: float = 120.0) -> None:
    """等待全部联调设备产生首批采集数据，避免驱动启动时序噪声。"""
    print("等待联调设备就绪…")
    deadline = time.monotonic() + timeout
    pending = set(MATRIX)
    while time.monotonic() < deadline and pending:
        for dev_id in list(pending):
            code, payload = el.get(f"/devices/{dev_id}/points")
            got = (unwrap_el(payload) or {}) if code == 200 else {}
            if got:
                pending.discard(dev_id)
        if pending:
            time.sleep(3)
    if pending:
        print(f"警告: 设备未就绪(超时): {sorted(pending)}")
    else:
        print("全部联调设备已就绪")


def phase_a_collect(pf: Client, el: Client, results: list) -> None:
    """阶段 A：源端写入 -> EdgeLite 采集一致性。"""
    print("\n===== 阶段 A：采集一致性（ProtoForge 源端 -> EdgeLite） =====")
    wait_devices_online(el)
    for dev_id, spec in MATRIX.items():
        pf_id = spec["pf"]
        points = spec["collect_points"]
        # 1) 向源端写入特征值
        write_ok = True
        for name, value in points.items():
            code, _ = pf.put(f"/devices/{pf_id}/points/{name}", {"value": value})
            if code != 200:
                write_ok = False
        if not write_ok:
            results.append(
                {
                    "phase": "A",
                    "device": dev_id,
                    "check": "source_write",
                    "pass": False,
                    "detail": "ProtoForge 写入失败",
                }
            )
            continue
        # 2) 等待采集周期
        time.sleep(COLLECT_WAIT_SECONDS)
        # 3) EdgeLite 读取比对
        got = el_points(el, dev_id)
        checks = {name: values_match(got.get(name), want) for name, want in points.items()}
        ok = write_ok and all(checks.values())
        results.append(
            {
                "phase": "A",
                "device": dev_id,
                "check": "collect_match",
                "pass": ok,
                "detail": {"expected": points, "got": {k: got.get(k) for k in points}},
            }
        )
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {dev_id}: 期望={points} 实际={ {k: got.get(k) for k in points} }")


def wire_read(reader: tuple, point: str):
    """用独立第三方协议客户端直读设备内存（不经过任何网关/REST）。

    背景：ProtoForge 的 REST 点位接口读的是"注册表"，与线上协议内存可能不同步
    （联调实测 Modbus 注册表残留旧值）。验收必须以线上内存为准。
    """
    kind = reader[0]
    if kind == "modbus":
        from pymodbus.client import ModbusTcpClient

        _, port, slave, regs = reader
        spec = regs[point]
        cli = ModbusTcpClient("127.0.0.1", port=port)
        try:
            cli.connect()
            if spec[0] == "hr":
                rr = cli.read_holding_registers(address=spec[1], count=1, device_id=slave)
            else:
                rr = cli.read_input_registers(address=spec[1], count=1, device_id=slave)
            return None if rr.isError() else rr.registers[0]
        finally:
            cli.close()
    if kind == "snap7":
        import snap7

        _, port, tags = reader
        plc = snap7.client.Client()
        plc.connect("127.0.0.1", 0, 1, port)
        try:
            db, byte = tags[point]
            data = plc.db_read(db, byte, 2)
            return int.from_bytes(data, "big", signed=True)
        finally:
            plc.disconnect()
    if kind == "mc":
        from pymcprotocol import Type3E

        _, port, tags = reader
        mc = Type3E(plctype="Q")
        mc.connect("127.0.0.1", port)
        try:
            return mc.batchread_wordunits(headdevice=tags[point], readsize=1)[0]
        finally:
            mc.close()
    if kind == "fins":
        import socket as _socket
        import struct as _struct

        _, port, tags = reader

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
            return recv_exact(s, _struct.unpack(">I", h[4:8])[0])

        s = _socket.create_connection(("127.0.0.1", port), timeout=5)
        try:
            init = _struct.pack(">I", 0) + _struct.pack(">I", 0) + _struct.pack(">I", 0)
            s.sendall(b"FINS" + _struct.pack(">I", len(init)) + init)
            recv_frame(s)
            fins_hdr = bytes([0x80, 0, 2, 0, 1, 0, 0, 0, 0, 1])
            data = bytes([0x82]) + _struct.pack(">H", tags[point]) + bytes([0]) + _struct.pack(">H", 1)
            body = _struct.pack(">I", 2) + _struct.pack(">I", 0) + fins_hdr + bytes([0x01, 0x01]) + data
            s.sendall(b"FINS" + _struct.pack(">I", len(body)) + body)
            r = recv_frame(s)
            # 响应: cmd(4)+err(4)+hdr(10)+mrc+src+end(2)+data -> 数据从偏移 22 开始
            return int.from_bytes(r[22:24], "big") if len(r) >= 24 else None
        finally:
            s.close()
    if kind == "pylogix":
        from pylogix import PLC

        _, port, tags = reader
        with PLC() as plc:
            plc.IPAddress = "127.0.0.1"
            plc.SocketTimeout = 5.0
            ret = plc.Read(tags[point])
            return ret.Value if ret and ret.Status == "Success" else None
    raise ValueError(f"unknown wire reader kind: {kind}")


def phase_b_write(pf: Client, el: Client, results: list) -> None:
    """阶段 B：EdgeLite 下写 -> 独立协议客户端直读设备内存验证。"""
    print("\n===== 阶段 B：下写链路（EdgeLite -> 设备线上内存，独立客户端验证） =====")
    for dev_id, spec in MATRIX.items():
        wp = spec.get("write_point")
        if not wp:
            continue
        name, value = wp
        code, payload = el.post(f"/devices/{dev_id}/points", {"point": name, "value": value})
        if code != 200:
            results.append(
                {
                    "phase": "B",
                    "device": dev_id,
                    "check": "el_write",
                    "pass": False,
                    "detail": f"HTTP {code}: {payload}",
                }
            )
            print(f"[FAIL] {dev_id}: EdgeLite 下写 {name}={value} -> HTTP {code}")
            continue
        time.sleep(1.5)  # 写后校验延迟 + 传播
        reader = spec.get("wire_reader")
        if reader is None:
            results.append(
                {
                    "phase": "B",
                    "device": dev_id,
                    "check": "write_readback",
                    "pass": True,
                    "detail": "no wire reader configured",
                }
            )
            continue
        err = None
        try:
            got = wire_read(reader, name)
        except Exception as e:
            got = None
            err = str(e)
        ok = err is None and values_match(got, value)
        results.append(
            {
                "phase": "B",
                "device": dev_id,
                "check": "write_readback",
                "pass": ok,
                "detail": {"wrote": value, "wire_value": got, "error": err},
            }
        )
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {dev_id}: EdgeLite 下写 {name}={value}，线上直读={got}" + (f"（{err}）" if err else ""))


def phase_c_fault(pf: Client, el: Client, results: list, target: str = "mc") -> None:
    """阶段 C：故障注入与恢复（停止/重启 ProtoForge 协议服务）。"""
    print(f"\n===== 阶段 C：故障注入与恢复（目标协议: {target}） =====")
    dev_ids = [d for d, s in MATRIX.items() if s["protocol"].endswith("mc") and target == "mc"]

    code, _ = pf.post(f"/protocols/{target}/stop")
    if code != 200:
        results.append(
            {"phase": "C", "device": dev_ids, "check": "protocol_stop", "pass": False, "detail": f"stop HTTP {code}"}
        )
        return
    print(f"  已停止 ProtoForge {target} 协议服务，等待 {FAULT_WAIT_SECONDS}s 观察降级…")
    time.sleep(FAULT_WAIT_SECONDS)

    health_by_dev = {}
    for dev_id in dev_ids:
        code, payload = el.get(f"/devices/{dev_id}/health")
        data = unwrap_el(payload) or {}
        health_by_dev[dev_id] = {
            "status_code": code,
            "is_connected": data.get("is_connected"),
            "consecutive_failures": data.get("consecutive_failures"),
        }
    code, _ = pf.post(f"/protocols/{target}/start")
    # FIXED: 恢复采用轮询等待。熔断器半开探测+退避重连需要 1-2 分钟量级（生产行为），
    # 固定等待窗口过短会把正常恢复误判为失败。
    print(f"  已重启 {target} 协议服务，轮询等待恢复（上限 {RECOVER_WAIT_SECONDS}s）…")
    deadline = time.monotonic() + RECOVER_WAIT_SECONDS
    recovered = {}
    while time.monotonic() < deadline:
        recovered = {dev_id: el_points(el, dev_id) for dev_id in dev_ids}
        if all(recovered.get(d) for d in dev_ids):
            break
        time.sleep(5)
    any_failures = any((h.get("consecutive_failures") or 0) > 0 for h in health_by_dev.values())
    # 验收标准：故障期间驱动感知到失败；恢复后能重新读到非空采集值
    recovery_ok = all(recovered.get(d) for d in dev_ids)
    results.append(
        {
            "phase": "C",
            "device": dev_ids,
            "check": "fault_detect_and_recover",
            "pass": bool(any_failures and recovery_ok),
            "detail": {"during_fault": health_by_dev, "after_recover": recovered},
        }
    )
    print(f"[{'PASS' if any_failures and recovery_ok else 'FAIL'}] 故障期健康={health_by_dev} 恢复后={recovered}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-write", action="store_true", help="跳过阶段 B 下写链路")
    parser.add_argument("--skip-fault", action="store_true", help="跳过阶段 C 故障注入")
    parser.add_argument("--report", default="joint_acceptance_report.json", help="JSON 报告输出路径")
    args = parser.parse_args()

    if not EL_PASS:
        print("错误：未设置 EL_PASS 环境变量（EdgeLite admin 密码）", file=sys.stderr)
        return 2

    pf = Client(PF, PF_USER, PF_PASS)
    el = Client(EL, EL_USER, EL_PASS, token_field="access_token")

    results: list[dict] = []
    started = datetime.now().isoformat()

    # 前置健康检查（健康端点无需认证，直接探测）
    def probe(url: str) -> int:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status

    for name, url in (("ProtoForge", f"{PF}/health"), ("EdgeLite", f"{EL.rsplit('/api/v1', 1)[0]}/health/ready")):
        try:
            code = probe(url)
            print(f"{name} 健康检查: HTTP {code}")
            if code != 200:
                results.append({"phase": "health", "device": name, "check": "up", "pass": False})
        except Exception as e:
            print(f"{name} 不可达: {e}", file=sys.stderr)
            return 2

    phase_a_collect(pf, el, results)
    if not args.skip_write:
        phase_b_write(pf, el, results)
    if not args.skip_fault:
        phase_c_fault(pf, el, results)

    passed = sum(1 for r in results if r["pass"])
    failed = sum(1 for r in results if not r["pass"])
    report = {
        "started_at": started,
        "finished_at": datetime.now().isoformat(),
        "passed": passed,
        "failed": failed,
        "results": results,
    }
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n===== 验收完成：{passed} 通过 / {failed} 失败，报告已写入 {args.report} =====")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
