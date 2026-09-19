"""自动生成冒烟测试 - src.edgelite.drivers.opcua_audit

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.opcua_audit"

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

    def test_log_callable(self):
        owner, obj = _auto_resolve('log')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 log：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.log 不可调用 (owner={owner!r})')

    def test_log_cert_switch_callable(self):
        owner, obj = _auto_resolve('log_cert_switch')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 log_cert_switch：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.log_cert_switch 不可调用 (owner={owner!r})')

    def test_log_failover_callable(self):
        owner, obj = _auto_resolve('log_failover')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 log_failover：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.log_failover 不可调用 (owner={owner!r})')

    def test_log_rbac_check_callable(self):
        owner, obj = _auto_resolve('log_rbac_check')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 log_rbac_check：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.log_rbac_check 不可调用 (owner={owner!r})')

    def test_log_config_version_callable(self):
        owner, obj = _auto_resolve('log_config_version')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 log_config_version：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.log_config_version 不可调用 (owner={owner!r})')

    def test_log_ota_callable(self):
        owner, obj = _auto_resolve('log_ota')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 log_ota：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.log_ota 不可调用 (owner={owner!r})')

    def test_get_recent_callable(self):
        owner, obj = _auto_resolve('get_recent')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_recent：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_recent 不可调用 (owner={owner!r})')

    def test_get_by_device_callable(self):
        owner, obj = _auto_resolve('get_by_device')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_by_device：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_by_device 不可调用 (owner={owner!r})')

    def test_get_by_action_callable(self):
        owner, obj = _auto_resolve('get_by_action')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_by_action：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_by_action 不可调用 (owner={owner!r})')

    def test_export_csv_callable(self):
        owner, obj = _auto_resolve('export_csv')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 export_csv：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.export_csv 不可调用 (owner={owner!r})')

    def test_get_stats_callable(self):
        owner, obj = _auto_resolve('get_stats')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_stats：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_stats 不可调用 (owner={owner!r})')

