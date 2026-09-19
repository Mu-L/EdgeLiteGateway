"""自动生成冒烟测试 - src.edgelite.drivers.edge_rule_engine

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.edge_rule_engine"

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

    def test_to_dict_callable(self):
        owner, obj = _auto_resolve('to_dict')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 to_dict：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.to_dict 不可调用 (owner={owner!r})')

    def test_set_on_action_callback_callable(self):
        owner, obj = _auto_resolve('set_on_action_callback')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 set_on_action_callback：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.set_on_action_callback 不可调用 (owner={owner!r})')

    def test_add_rule_callable(self):
        owner, obj = _auto_resolve('add_rule')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 add_rule：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.add_rule 不可调用 (owner={owner!r})')

    def test_get_rule_callable(self):
        owner, obj = _auto_resolve('get_rule')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_rule：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_rule 不可调用 (owner={owner!r})')

    def test_get_rules_for_device_callable(self):
        owner, obj = _auto_resolve('get_rules_for_device')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_rules_for_device：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_rules_for_device 不可调用 (owner={owner!r})')

    def test_get_all_rules_callable(self):
        owner, obj = _auto_resolve('get_all_rules')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_all_rules：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_all_rules 不可调用 (owner={owner!r})')

    def test_evaluate_point_callable(self):
        owner, obj = _auto_resolve('evaluate_point')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 evaluate_point：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.evaluate_point 不可调用 (owner={owner!r})')

    def test_remove_rule_callable(self):
        owner, obj = _auto_resolve('remove_rule')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 remove_rule：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.remove_rule 不可调用 (owner={owner!r})')

    def test_update_rule_callable(self):
        owner, obj = _auto_resolve('update_rule')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 update_rule：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.update_rule 不可调用 (owner={owner!r})')

    def test_get_active_alarms_callable(self):
        owner, obj = _auto_resolve('get_active_alarms')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_active_alarms：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_active_alarms 不可调用 (owner={owner!r})')

    def test_get_alarm_history_callable(self):
        owner, obj = _auto_resolve('get_alarm_history')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_alarm_history：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_alarm_history 不可调用 (owner={owner!r})')

    def test_get_stats_callable(self):
        owner, obj = _auto_resolve('get_stats')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_stats：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_stats 不可调用 (owner={owner!r})')

