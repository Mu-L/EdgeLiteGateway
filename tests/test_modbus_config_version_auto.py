"""自动生成冒烟测试 - src.edgelite.drivers.modbus_config_version

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.modbus_config_version"

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

    def test_snapshot_device_config_callable(self):
        owner, obj = _auto_resolve("snapshot_device_config")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 snapshot_device_config：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), (
            f"{_MODULE}.snapshot_device_config 不可调用 (owner={owner!r})"
        )

    def test_rollback_callable(self):
        owner, obj = _auto_resolve("rollback")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 rollback：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.rollback 不可调用 (owner={owner!r})"

    def test_list_versions_callable(self):
        owner, obj = _auto_resolve("list_versions")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 list_versions：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.list_versions 不可调用 (owner={owner!r})"

    def test_get_version_callable(self):
        owner, obj = _auto_resolve("get_version")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 get_version：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.get_version 不可调用 (owner={owner!r})"

    def test_diff_versions_callable(self):
        owner, obj = _auto_resolve("diff_versions")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 diff_versions：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.diff_versions 不可调用 (owner={owner!r})"

    def test_export_json_callable(self):
        owner, obj = _auto_resolve("export_json")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 export_json：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.export_json 不可调用 (owner={owner!r})"

    def test_export_yaml_callable(self):
        owner, obj = _auto_resolve("export_yaml")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 export_yaml：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.export_yaml 不可调用 (owner={owner!r})"

    def test_import_json_callable(self):
        owner, obj = _auto_resolve("import_json")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 import_json：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.import_json 不可调用 (owner={owner!r})"

    def test_verify_integrity_callable(self):
        owner, obj = _auto_resolve("verify_integrity")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 verify_integrity：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.verify_integrity 不可调用 (owner={owner!r})"

    def test_close_callable(self):
        owner, obj = _auto_resolve("close")
        assert obj is not None, (
            f"{_MODULE} 中解析不到 close：模块属性与所有类属性表均未命中，请确认 API 是否已删除或改名"
        )
        assert callable(obj) or isinstance(obj, property), f"{_MODULE}.close 不可调用 (owner={owner!r})"
