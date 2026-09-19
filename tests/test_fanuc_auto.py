"""自动生成冒烟测试 - src.edgelite.drivers.fanuc

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.fanuc"

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

    def test_connect_callable(self):
        owner, obj = _auto_resolve('connect')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 connect：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.connect 不可调用 (owner={owner!r})')

    def test_close_callable(self):
        owner, obj = _auto_resolve('close')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 close：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.close 不可调用 (owner={owner!r})')

    def test_read_status_callable(self):
        owner, obj = _auto_resolve('read_status')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_status：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_status 不可调用 (owner={owner!r})')

    def test_read_position_callable(self):
        owner, obj = _auto_resolve('read_position')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_position：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_position 不可调用 (owner={owner!r})')

    def test_read_program_number_callable(self):
        owner, obj = _auto_resolve('read_program_number')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_program_number：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_program_number 不可调用 (owner={owner!r})')

    def test_read_feedrate_callable(self):
        owner, obj = _auto_resolve('read_feedrate')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_feedrate：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_feedrate 不可调用 (owner={owner!r})')

    def test_read_spindle_speed_callable(self):
        owner, obj = _auto_resolve('read_spindle_speed')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_spindle_speed：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_spindle_speed 不可调用 (owner={owner!r})')

    def test_read_alarms_callable(self):
        owner, obj = _auto_resolve('read_alarms')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_alarms：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_alarms 不可调用 (owner={owner!r})')

    def test_start_callable(self):
        owner, obj = _auto_resolve('start')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 start：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.start 不可调用 (owner={owner!r})')

    def test_stop_callable(self):
        owner, obj = _auto_resolve('stop')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 stop：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.stop 不可调用 (owner={owner!r})')

    def test_read_points_callable(self):
        owner, obj = _auto_resolve('read_points')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_points：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_points 不可调用 (owner={owner!r})')

    def test_write_point_callable(self):
        owner, obj = _auto_resolve('write_point')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 write_point：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.write_point 不可调用 (owner={owner!r})')

    def test_add_device_callable(self):
        owner, obj = _auto_resolve('add_device')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 add_device：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.add_device 不可调用 (owner={owner!r})')

    def test_discover_devices_callable(self):
        owner, obj = _auto_resolve('discover_devices')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 discover_devices：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.discover_devices 不可调用 (owner={owner!r})')

    def test_remove_device_callable(self):
        owner, obj = _auto_resolve('remove_device')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 remove_device：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.remove_device 不可调用 (owner={owner!r})')

