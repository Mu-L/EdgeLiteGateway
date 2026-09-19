"""共享测试辅助函数（无桩依赖、可独立导入）。

FIXED(ci): 原先 make_app / make_mock_audit_service 定义在 conftest.py，
tests/ 与 e2e/ 均无 __init__.py 且 testpaths 同时包含两个目录，
`from conftest import ...` 在 CI 中会因 sys.modules 的 "conftest" 名字
先到先得而解析到 e2e/conftest.py，导致 ImportError 或桩类重复执行
（曾导致 test_mqtt_forwarder 重新 exec conftest 后覆盖
edgelite.platform.north_base 桩，进而污染 test_platform_service）。
统一从本模块导入，模块名唯一无冲突。
"""

from __future__ import annotations

from typing import Any


def make_mock_audit_service():
    """返回带 log 方法的 mock 审计服务，供需要 audit_service 的端点测试使用。"""
    from unittest.mock import AsyncMock

    svc = AsyncMock()
    svc.log = AsyncMock(return_value=None)
    return svc


def make_app(router: Any = None, role: str = "admin", services: dict | None = None):
    """构建测试用 FastAPI 应用：覆盖认证依赖 + 注入 mock 服务。

    Args:
        router: 要挂载的 APIRouter（None 时挂载空应用，仅用于依赖测试）
        role: 覆盖认证用户的角色（admin/operator/viewer）
        services: 注入 app.state 的服务字典
    """
    import os

    from fastapi import FastAPI

    from edgelite.api.deps import get_current_user

    os.environ.setdefault("EDGELITE_SECURITY__SECRET_KEY", "test-secret-key-for-testing-only-32chars!")
    os.environ.setdefault("DEV_MODE", "true")

    app = FastAPI(title="EdgeLite Test")
    if router is not None:
        app.include_router(router)

    # 覆盖认证依赖：require_permission 内部依赖 get_current_user
    user = {"user_id": "test-admin", "username": "testadmin", "role": role}
    app.dependency_overrides[get_current_user] = lambda: user

    # 注入服务到 app.state
    if services:
        for key, value in services.items():
            setattr(app.state, key, value)

    return app
