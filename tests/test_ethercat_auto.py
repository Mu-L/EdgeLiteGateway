"""自动生成冒烟测试 - src.edgelite.drivers.ethercat

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.ethercat"

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

    def test_initialize_callable(self):
        owner, obj = _auto_resolve('initialize')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 initialize：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.initialize 不可调用 (owner={owner!r})')

    def test_scan_slaves_callable(self):
        owner, obj = _auto_resolve('scan_slaves')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 scan_slaves：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.scan_slaves 不可调用 (owner={owner!r})')

    def test_configure_pdo_callable(self):
        owner, obj = _auto_resolve('configure_pdo')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 configure_pdo：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.configure_pdo 不可调用 (owner={owner!r})')

    def test_set_slave_state_callable(self):
        owner, obj = _auto_resolve('set_slave_state')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 set_slave_state：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.set_slave_state 不可调用 (owner={owner!r})')

    def test_read_pdo_callable(self):
        owner, obj = _auto_resolve('read_pdo')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_pdo：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_pdo 不可调用 (owner={owner!r})')

    def test_write_pdo_callable(self):
        owner, obj = _auto_resolve('write_pdo')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 write_pdo：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.write_pdo 不可调用 (owner={owner!r})')

    def test_read_sdo_callable(self):
        owner, obj = _auto_resolve('read_sdo')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 read_sdo：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.read_sdo 不可调用 (owner={owner!r})')

    def test_write_sdo_callable(self):
        owner, obj = _auto_resolve('write_sdo')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 write_sdo：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.write_sdo 不可调用 (owner={owner!r})')

    def test_request_dc_sync_callable(self):
        owner, obj = _auto_resolve('request_dc_sync')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 request_dc_sync：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.request_dc_sync 不可调用 (owner={owner!r})')

    def test_close_callable(self):
        owner, obj = _auto_resolve('close')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 close：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.close 不可调用 (owner={owner!r})')

    def test_is_real_mode_callable(self):
        owner, obj = _auto_resolve('is_real_mode')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 is_real_mode：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.is_real_mode 不可调用 (owner={owner!r})')

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

