#!/usr/bin/env python3
"""EdgeLite 冒烟测试 — 部署后核心流程验证。

用法:
    python scripts/smoke_test.py --base-url http://localhost:8080
    python scripts/smoke_test.py --base-url https://api.example.com --user admin --pass secret

退出码:
    0 — 所有冒烟测试通过
    1 — 一个或多个测试失败
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx

# FIXED-CI2: 首登强制改密流程完成后的新密码（仅 CI 冒烟环境使用；
# 重试时直接用该密码登录，因为第一次尝试已完成改密）
CHANGED_PASSWORD = "Smoke@Test2026"


def smoke_test(base_url: str, username: str, password: str) -> bool:
    """执行冒烟测试套件，返回是否全部通过。"""
    results: list[tuple[str, bool, str]] = []
    client = httpx.Client(base_url=base_url, timeout=10.0)

    # ── 1. Liveness 健康检查 ──────────────────────────────────────────
    try:
        r = client.get("/health/live")
        ok = r.status_code == 200 and r.json().get("status") == "ok"
        results.append(("health/live", ok, f"HTTP {r.status_code}"))
    except Exception as e:
        results.append(("health/live", False, str(e)))

    # ── 2. Readiness 健康检查 ─────────────────────────────────────────
    # FIXED-CI: 原请求 /health（完整检查）— 该端点设计上 degraded 也返 503，
    # 无 InfluxDB/MQTT broker 的最小部署永远失败；探针语义对应 /health/ready
    # （仅检查 SQLite+InfluxDB+磁盘，降级视为可就绪）[2026-09-19]
    try:
        r = client.get("/health/ready")
        ok = r.status_code == 200
        results.append(("health/ready", ok, f"HTTP {r.status_code}"))
    except Exception as e:
        results.append(("health/ready", False, str(e)))

    # ── 3. 登录获取 Token ─────────────────────────────────────────────
    # FIXED-CI: 路径对齐现网 /api/v1/auth/login（旧 /api/* 已不存在，旧行为
    # 误报 403 CSRF — 实为命中未豁免的旧路径）[2026-09-19]
    # FIXED-CI2: 全新初始化的 admin 带 must_change_password 标记，除改密/
    # me/logout 外一律 403 ERR_AUTH_MUST_CHANGE_PASSWORD — 冒烟需走完整
    # 首登改密流程再测受保护端点 [2026-09-19]
    token = None
    used_password = password
    for candidate in (password, CHANGED_PASSWORD):
        try:
            r = client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": candidate},
            )
            if r.status_code == 200:
                data = r.json()
                token = data.get("data", {}).get("access_token") or data.get("access_token")
                used_password = candidate
                results.append(("auth/login", token is not None, f"HTTP 200 token={'yes' if token else 'no'}"))
                break
            if candidate is password:
                results.append(("auth/login", False, f"HTTP {r.status_code}: {r.text[:100]}"))
        except Exception as e:
            results.append(("auth/login", False, str(e)))
            break

    # ── 4. 首登强制改密（若触发）──────────────────────────────────────
    if token:
        try:
            headers0 = {"Authorization": f"Bearer {token}"}
            r = client.get("/api/v1/auth/me", headers=headers0)
            csrf = r.headers.get("X-CSRF-Token", "")
            need_change = r.status_code == 200 and r.json().get("data", {}).get("must_change_password")
            if need_change:
                r2 = client.post(
                    "/api/v1/auth/change-password",
                    json={"old_password": used_password, "new_password": CHANGED_PASSWORD},
                    headers={**headers0, "X-CSRF-Token": csrf},
                )
                if r2.status_code == 200:
                    # 旧 token 因 pwd_changed_ts 已失效，用新密码重新登录
                    r3 = client.post(
                        "/api/v1/auth/login",
                        json={"username": username, "password": CHANGED_PASSWORD},
                    )
                    token = r3.json().get("data", {}).get("access_token") if r3.status_code == 200 else None
                    relogin = "ok" if token else "fail"
                    results.append(
                        ("first-login password change", token is not None, f"HTTP {r2.status_code} relogin={relogin}")
                    )
                else:
                    results.append(("first-login password change", False, f"HTTP {r2.status_code}: {r2.text[:100]}"))
        except Exception as e:
            results.append(("first-login password change", False, str(e)))

    # ── 4. 设备列表（需要认证）─────────────────────────────────────────
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            r = client.get("/api/v1/devices", headers=headers)
            ok = r.status_code == 200
            results.append(("GET /api/v1/devices", ok, f"HTTP {r.status_code}"))
        except Exception as e:
            results.append(("GET /api/v1/devices", False, str(e)))

        # ── 5. 系统信息 ───────────────────────────────────────────────
        try:
            r = client.get("/api/v1/system/status", headers=headers)
            ok = r.status_code == 200
            results.append(("GET /api/v1/system/status", ok, f"HTTP {r.status_code}"))
        except Exception as e:
            results.append(("GET /api/v1/system/status", False, str(e)))

        # ── 6. 指标端点 (Prometheus) ──────────────────────────────────
        # FIXED-CI: 现网路径为 /api/v1/metrics 且需认证 [2026-09-19]
        try:
            r = client.get("/api/v1/metrics", headers=headers)
            ok = r.status_code == 200 and "# HELP" in r.text
            results.append(("GET /api/v1/metrics", ok, f"HTTP {r.status_code} len={len(r.text)}"))
        except Exception as e:
            results.append(("GET /api/v1/metrics", False, str(e)))
    else:
        for endpoint in ["GET /api/v1/devices", "GET /api/v1/system/status", "GET /api/v1/metrics"]:
            results.append((endpoint, False, "skipped: no auth token"))

    client.close()

    # ── 输出结果 ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  EdgeLite Smoke Test — {base_url}")
    print("=" * 60)
    all_pass = True
    for name, ok, detail in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name:30s}  {detail}")
        if not ok:
            all_pass = False
    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"  结果: {passed}/{total} 通过")
    print("=" * 60 + "\n")
    return all_pass


def main():
    parser = argparse.ArgumentParser(description="EdgeLite 冒烟测试")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("EDGELITE_TEST_BASE", "http://127.0.0.1:8080"),
        help="EdgeLite 基础 URL (默认: http://127.0.0.1:8080)",
    )
    parser.add_argument(
        "--user",
        default=os.environ.get("EDGELITE_TEST_USER", "admin"),
        help="测试用户名 (默认: admin)",
    )
    parser.add_argument(
        "--pass",
        dest="password",
        default=os.environ.get("EDGELITE_TEST_PASS", "admin"),
        help="测试密码 (默认: admin)",
    )
    parser.add_argument(
        "--retry",
        type=int,
        default=3,
        help="重试次数（服务可能还在启动中）",
    )
    args = parser.parse_args()

    for attempt in range(1, args.retry + 1):
        print(f"\n🧪 冒烟测试尝试 {attempt}/{args.retry}...")
        if smoke_test(args.base_url, args.user, args.password):
            sys.exit(0)
        if attempt < args.retry:
            print("⏳ 等待 10 秒后重试...")
            time.sleep(10)

    sys.exit(1)


if __name__ == "__main__":
    main()
