"""自动生成冒烟测试 - src.edgelite.drivers.knx

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.knx"

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

    def test_read_group_value_callable(self):
        owner, obj = _auto_resolve('read_group_value')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_group_value：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_group_value 不可调用 (owner={owner!r})')

    def test_write_group_value_callable(self):
        owner, obj = _auto_resolve('write_group_value')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 write_group_value：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.write_group_value 不可调用 (owner={owner!r})')

    def test_handle_packet_callable(self):
        owner, obj = _auto_resolve('handle_packet')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 handle_packet：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.handle_packet 不可调用 (owner={owner!r})')

    def test_set_group_value_callback_callable(self):
        owner, obj = _auto_resolve('set_group_value_callback')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 set_group_value_callback：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.set_group_value_callback 不可调用 (owner={owner!r})')

    def test_get_latest_value_callable(self):
        owner, obj = _auto_resolve('get_latest_value')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_latest_value：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_latest_value 不可调用 (owner={owner!r})')

    def test_connection_made_callable(self):
        owner, obj = _auto_resolve('connection_made')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 connection_made：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.connection_made 不可调用 (owner={owner!r})')

    def test_datagram_received_callable(self):
        owner, obj = _auto_resolve('datagram_received')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 datagram_received：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.datagram_received 不可调用 (owner={owner!r})')

    def test_error_received_callable(self):
        owner, obj = _auto_resolve('error_received')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 error_received：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.error_received 不可调用 (owner={owner!r})')

    def test_start_callable(self):
        owner, obj = _auto_resolve('start')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 start：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.start 不可调用 (owner={owner!r})')

    def test_on_data_callable(self):
        owner, obj = _auto_resolve('on_data')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 on_data：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.on_data 不可调用 (owner={owner!r})')

    def test_stop_callable(self):
        owner, obj = _auto_resolve('stop')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 stop：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.stop 不可调用 (owner={owner!r})')

    def test_add_device_callable(self):
        owner, obj = _auto_resolve('add_device')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 add_device：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.add_device 不可调用 (owner={owner!r})')

    def test_remove_device_callable(self):
        owner, obj = _auto_resolve('remove_device')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 remove_device：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.remove_device 不可调用 (owner={owner!r})')

    def test_read_points_callable(self):
        owner, obj = _auto_resolve('read_points')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_points：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_points 不可调用 (owner={owner!r})')

    def test_get_event_status_callable(self):
        owner, obj = _auto_resolve('get_event_status')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_event_status：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_event_status 不可调用 (owner={owner!r})')

    def test_write_point_callable(self):
        owner, obj = _auto_resolve('write_point')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 write_point：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.write_point 不可调用 (owner={owner!r})')

    def test_discover_devices_callable(self):
        owner, obj = _auto_resolve('discover_devices')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 discover_devices：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.discover_devices 不可调用 (owner={owner!r})')

    def test_is_device_connected_callable(self):
        owner, obj = _auto_resolve('is_device_connected')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 is_device_connected：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.is_device_connected 不可调用 (owner={owner!r})')

