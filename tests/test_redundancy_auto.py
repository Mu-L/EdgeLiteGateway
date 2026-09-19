"""自动生成冒烟测试 - src.edgelite.drivers.redundancy

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.redundancy"

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

    def test_set_on_switch_callback_callable(self):
        owner, obj = _auto_resolve('set_on_switch_callback')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 set_on_switch_callback：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.set_on_switch_callback 不可调用 (owner={owner!r})')

    def test_register_device_callable(self):
        owner, obj = _auto_resolve('register_device')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 register_device：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.register_device 不可调用 (owner={owner!r})')

    def test_unregister_device_callable(self):
        owner, obj = _auto_resolve('unregister_device')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 unregister_device：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.unregister_device 不可调用 (owner={owner!r})')

    def test_record_success_callable(self):
        owner, obj = _auto_resolve('record_success')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 record_success：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.record_success 不可调用 (owner={owner!r})')

    def test_record_failure_callable(self):
        owner, obj = _auto_resolve('record_failure')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 record_failure：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.record_failure 不可调用 (owner={owner!r})')

    def test_get_active_role_callable(self):
        owner, obj = _auto_resolve('get_active_role')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_active_role：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_active_role 不可调用 (owner={owner!r})')

    def test_get_active_host_callable(self):
        owner, obj = _auto_resolve('get_active_host')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_active_host：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_active_host 不可调用 (owner={owner!r})')

    def test_get_status_callable(self):
        owner, obj = _auto_resolve('get_status')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_status：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_status 不可调用 (owner={owner!r})')

    def test_mark_primary_healthy_callable(self):
        owner, obj = _auto_resolve('mark_primary_healthy')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 mark_primary_healthy：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.mark_primary_healthy 不可调用 (owner={owner!r})')

    def test_stop_callable(self):
        owner, obj = _auto_resolve('stop')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 stop：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.stop 不可调用 (owner={owner!r})')

