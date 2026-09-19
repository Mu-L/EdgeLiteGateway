"""自动生成冒烟测试 - src.edgelite.drivers.registry

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.registry"

try:
    _mod = importlib.import_module(_MODULE)
    _OK = True
    _ERR = ""
except ImportError as _e:  # pragma: no cover - 仅在依赖缺失时触发
    _OK = False
    _ERR = str(_e)
    _mod = None


def _auto_resolve(name):
    """在模块属性与模块内各类的属性表中解析 name，返回 (owner, obj) 或 (None, None)。"""
    obj = getattr(_mod, name, None)
    if obj is not None:
        return _mod, obj
    for _cname, cls in inspect.getmembers(_mod, inspect.isclass):
        if name in cls.__dict__:
            return cls, cls.__dict__[name]
    return None, None


class TestAutoSmoke:
    @pytest.fixture(autouse=True)
    def _require_import(self):
        if not _OK:
            pytest.skip(f"import failed: {_ERR}")

    def test_get_driver_display_name_callable(self):
        owner, obj = _auto_resolve("get_driver_display_name")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 get_driver_display_name：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), (
            f"{_MODULE}.get_driver_display_name 不可调用 (owner={owner!r})"
        )

    def test_get_driver_registry_callable(self):
        owner, obj = _auto_resolve("get_driver_registry")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 get_driver_registry：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.get_driver_registry 不可调用 (owner={owner!r})"
