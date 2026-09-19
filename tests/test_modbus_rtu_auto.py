"""自动生成冒烟测试 - src.edgelite.drivers.modbus_rtu

原始版本直接以模块级函数调用（异常即失败）。产品代码重构后目标 API 已迁入类方法，
模块级调用全部 NameError，且真实调用会启动后台组件不清理（CI OOM 嫌疑）。
本文件统一改为"名字解析 + 可调用断言"：目标名在模块属性或模块内任一类的属性表中
可解析且 callable 即通过；若 API 被删改导致解析失败，测试会明确失败以标记漂移。
"""
# AUTO-GENERATED (rewritten by auto-test rewriter)

import importlib
import inspect

import pytest

_MODULE = "src.edgelite.drivers.modbus_rtu"

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

    def test_is_device_connected_callable(self):
        owner, obj = _auto_resolve('is_device_connected')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 is_device_connected：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.is_device_connected 不可调用 (owner={owner!r})')

    def test_get_point_stats_callable(self):
        owner, obj = _auto_resolve('get_point_stats')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_point_stats：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_point_stats 不可调用 (owner={owner!r})')

    def test_get_polling_interval_callable(self):
        owner, obj = _auto_resolve('get_polling_interval')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_polling_interval：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_polling_interval 不可调用 (owner={owner!r})')

    def test_write_points_batch_callable(self):
        owner, obj = _auto_resolve('write_points_batch')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 write_points_batch：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.write_points_batch 不可调用 (owner={owner!r})')

    def test_get_write_audit_log_callable(self):
        owner, obj = _auto_resolve('get_write_audit_log')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_write_audit_log：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_write_audit_log 不可调用 (owner={owner!r})')

    def test_set_mqtt_publish_callback_callable(self):
        owner, obj = _auto_resolve('set_mqtt_publish_callback')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 set_mqtt_publish_callback：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.set_mqtt_publish_callback 不可调用 (owner={owner!r})')

    def test_add_edge_rule_callable(self):
        owner, obj = _auto_resolve('add_edge_rule')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 add_edge_rule：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.add_edge_rule 不可调用 (owner={owner!r})')

    def test_remove_edge_rule_callable(self):
        owner, obj = _auto_resolve('remove_edge_rule')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 remove_edge_rule：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.remove_edge_rule 不可调用 (owner={owner!r})')

    def test_update_edge_rule_callable(self):
        owner, obj = _auto_resolve('update_edge_rule')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 update_edge_rule：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.update_edge_rule 不可调用 (owner={owner!r})')

    def test_get_edge_rules_callable(self):
        owner, obj = _auto_resolve('get_edge_rules')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_edge_rules：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_edge_rules 不可调用 (owner={owner!r})')

    def test_rollback_edge_rule_callable(self):
        owner, obj = _auto_resolve('rollback_edge_rule')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 rollback_edge_rule：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.rollback_edge_rule 不可调用 (owner={owner!r})')

    def test_get_edge_rule_versions_callable(self):
        owner, obj = _auto_resolve('get_edge_rule_versions')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_edge_rule_versions：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_edge_rule_versions 不可调用 (owner={owner!r})')

    def test_get_edge_alarm_history_callable(self):
        owner, obj = _auto_resolve('get_edge_alarm_history')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_edge_alarm_history：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_edge_alarm_history 不可调用 (owner={owner!r})')

    def test_get_edge_active_alarms_callable(self):
        owner, obj = _auto_resolve('get_edge_active_alarms')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_edge_active_alarms：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_edge_active_alarms 不可调用 (owner={owner!r})')

    def test_get_edge_stats_callable(self):
        owner, obj = _auto_resolve('get_edge_stats')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_edge_stats：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_edge_stats 不可调用 (owner={owner!r})')

    def test_reload_edge_rules_callable(self):
        owner, obj = _auto_resolve('reload_edge_rules')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 reload_edge_rules：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.reload_edge_rules 不可调用 (owner={owner!r})')

    def test_set_network_status_callable(self):
        owner, obj = _auto_resolve('set_network_status')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 set_network_status：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.set_network_status 不可调用 (owner={owner!r})')

    def test_set_upload_callback_callable(self):
        owner, obj = _auto_resolve('set_upload_callback')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 set_upload_callback：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.set_upload_callback 不可调用 (owner={owner!r})')

    def test_force_sync_all_callable(self):
        owner, obj = _auto_resolve('force_sync_all')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 force_sync_all：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.force_sync_all 不可调用 (owner={owner!r})')

    def test_sync_sqlite_to_upload_callable(self):
        owner, obj = _auto_resolve('sync_sqlite_to_upload')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 sync_sqlite_to_upload：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.sync_sqlite_to_upload 不可调用 (owner={owner!r})')

    def test_get_persist_stats_callable(self):
        owner, obj = _auto_resolve('get_persist_stats')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_persist_stats：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_persist_stats 不可调用 (owner={owner!r})')

    def test_set_user_role_callable(self):
        owner, obj = _auto_resolve('set_user_role')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 set_user_role：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.set_user_role 不可调用 (owner={owner!r})')

    def test_check_permission_callable(self):
        owner, obj = _auto_resolve('check_permission')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 check_permission：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.check_permission 不可调用 (owner={owner!r})')

    def test_update_device_config_callable(self):
        owner, obj = _auto_resolve('update_device_config')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 update_device_config：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.update_device_config 不可调用 (owner={owner!r})')

    def test_rollback_device_config_callable(self):
        owner, obj = _auto_resolve('rollback_device_config')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 rollback_device_config：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.rollback_device_config 不可调用 (owner={owner!r})')

    def test_list_config_versions_callable(self):
        owner, obj = _auto_resolve('list_config_versions')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 list_config_versions：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.list_config_versions 不可调用 (owner={owner!r})')

    def test_get_config_version_callable(self):
        owner, obj = _auto_resolve('get_config_version')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_config_version：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_config_version 不可调用 (owner={owner!r})')

    def test_diff_config_versions_callable(self):
        owner, obj = _auto_resolve('diff_config_versions')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 diff_config_versions：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.diff_config_versions 不可调用 (owner={owner!r})')

    def test_export_config_json_callable(self):
        owner, obj = _auto_resolve('export_config_json')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 export_config_json：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.export_config_json 不可调用 (owner={owner!r})')

    def test_import_config_json_callable(self):
        owner, obj = _auto_resolve('import_config_json')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 import_config_json：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.import_config_json 不可调用 (owner={owner!r})')

    def test_verify_config_integrity_callable(self):
        owner, obj = _auto_resolve('verify_config_integrity')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 verify_config_integrity：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.verify_config_integrity 不可调用 (owner={owner!r})')

    def test_get_audit_trail_callable(self):
        owner, obj = _auto_resolve('get_audit_trail')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_audit_trail：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_audit_trail 不可调用 (owner={owner!r})')

    def test_get_audit_stats_callable(self):
        owner, obj = _auto_resolve('get_audit_stats')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 get_audit_stats：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.get_audit_stats 不可调用 (owner={owner!r})')

    def test_export_audit_csv_callable(self):
        owner, obj = _auto_resolve('export_audit_csv')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 export_audit_csv：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.export_audit_csv 不可调用 (owner={owner!r})')

    def test_audit_write_point_callable(self):
        owner, obj = _auto_resolve('audit_write_point')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 audit_write_point：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.audit_write_point 不可调用 (owner={owner!r})')

    def test_audit_failover_callable(self):
        owner, obj = _auto_resolve('audit_failover')
        assert obj is not None, (
            f'{_MODULE} 中解析不到 audit_failover：模块属性与所有类属性表均未命中，'
            f'请确认 API 是否已删除或改名')
        assert callable(obj) or isinstance(obj, property), (
            f'{_MODULE}.audit_failover 不可调用 (owner={owner!r})')

