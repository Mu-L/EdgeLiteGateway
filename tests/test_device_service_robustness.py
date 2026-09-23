"""设备驱动健壮性修复测试

覆盖 FIXED-ROBUST-01/02/03/04 四项修复：
1. FIXED-ROBUST-01: DeviceService.start_collect 对驱动实例缺失的设备按需重建驱动
   （原实现抛 "Device driver not found"，启动期连接失败的 S7/MC 设备永久无法恢复）；
2. FIXED-ROBUST-02: load_existing_devices 模拟器 add_device 参数错传修复
   （points 误传为 config 形参，重启后模拟器设备点位表为空、无数据）；
3. FIXED-ROBUST-03: FINS 驱动补齐缺失的 _is_bit_access 方法
   （原调用未定义方法，AttributeError 被吞后恒走 fallback 慢路径）；
4. FIXED-ROBUST-04: api/devices.py 不再调用 DriverRegistry 上不存在的
   get_driver_instance（写策略与设备可观测性指标死代码路径）。
"""

from __future__ import annotations

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, "src")

from edgelite.drivers.base import DriverCapabilities, DriverHealthStats  # noqa: E402
from edgelite.services.device_service import DeviceService  # noqa: E402


# ───────────────────────── 辅助与夹具 ─────────────────────────


def _make_mock_driver(*, connected: bool = True, start_side_effect: Exception | None = None) -> MagicMock:
    drv = MagicMock()
    drv.start = AsyncMock(return_value=None)
    if start_side_effect is not None:
        drv.start.side_effect = start_side_effect
    drv.stop = AsyncMock(return_value=None)
    drv.add_device = AsyncMock(return_value=None)
    drv.read_points = AsyncMock(return_value={})
    drv.is_device_connected = MagicMock(return_value=connected)
    drv.capabilities = DriverCapabilities(read=True, write=True)
    drv.get_health_stats = MagicMock(return_value=DriverHealthStats(device_id="d1"))
    return drv


@pytest.fixture
def device_repo():
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    repo.list_all = AsyncMock(return_value=([], 0))
    repo.update_status = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=True)
    repo.cleanup_sidecar_data = AsyncMock(return_value=None)
    repo.retry_pending_sidecar_cleanups = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def rule_repo():
    repo = AsyncMock()
    repo.list_all = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def scheduler():
    sch = AsyncMock()
    sch.start_collect = AsyncMock(return_value=None)
    sch.stop_collect = AsyncMock(return_value=None)
    sch.get_last_values = AsyncMock(return_value={})
    return sch


@pytest.fixture
def lifecycle():
    lc = AsyncMock()
    lc.on_device_online = AsyncMock(return_value=None)
    lc.on_device_offline = AsyncMock(return_value=None)
    lc.remove_device = AsyncMock(return_value=None)
    return lc


@pytest.fixture
def template_repo():
    repo = AsyncMock()
    repo.create = AsyncMock(return_value={"name": "tpl"})
    repo.list_all = AsyncMock(return_value=([], 0))
    repo.get = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def registry():
    reg = MagicMock()
    reg.get_driver_class = MagicMock(return_value=None)
    reg.get_all_protocol_keys = MagicMock(return_value=["modbus_tcp"])
    return reg


@pytest.fixture
def device_service(device_repo, rule_repo, scheduler, lifecycle, template_repo, registry):
    with patch("edgelite.services.device_service.get_driver_registry", return_value=registry):
        svc = DeviceService(
            device_repo=device_repo,
            rule_repo=rule_repo,
            scheduler=scheduler,
            lifecycle=lifecycle,
            template_repo=template_repo,
        )
    return svc


@pytest.fixture
def mock_simulator():
    drv = MagicMock()
    drv.start = AsyncMock(return_value=None)
    drv.add_device = AsyncMock(return_value=None)
    drv.remove_device = AsyncMock(return_value=None)
    drv.read_points = AsyncMock(return_value={})
    drv.is_device_connected = MagicMock(return_value=True)
    drv.capabilities = DriverCapabilities(read=True, write=True)
    drv.get_health_stats = MagicMock(return_value=DriverHealthStats(device_id="sim"))
    return drv


# ───────────────────────── FIXED-ROBUST-01: 按需重建驱动 ─────────────────────────


class TestStartCollectRecreateDriver:
    """start_collect 驱动实例缺失时按需重建"""

    async def test_recreates_missing_driver_and_starts_collect(
        self, device_service, device_repo, scheduler, lifecycle, registry
    ):
        """启动期 start 失败的设备（无驱动实例）再次 start-collect 应重建驱动并恢复采集"""
        drv = _make_mock_driver()
        driver_cls = MagicMock(return_value=drv)
        registry.get_driver_class = MagicMock(return_value=driver_cls)
        device_repo.get = AsyncMock(
            return_value={
                "device_id": "pf-s7",
                "protocol": "siemens_s7",
                "config": {"host": "127.0.0.1"},
                "points": [{"name": "temp"}],
                "collect_interval": 5,
                "status": "offline",
            }
        )

        ok = await device_service.start_collect("pf-s7")

        assert ok is True
        driver_cls.assert_called_once_with()
        drv.start.assert_awaited_once_with({"host": "127.0.0.1"})
        drv.add_device.assert_awaited_once_with("pf-s7", {"host": "127.0.0.1"}, [{"name": "temp"}])
        assert device_service._driver_instances["pf-s7"] is drv
        scheduler.start_collect.assert_awaited_once()
        lifecycle.on_device_online.assert_awaited_once_with("pf-s7")
        device_repo.update_status.assert_awaited_once_with("pf-s7", "online")

    async def test_raises_informative_error_when_driver_start_fails(
        self, device_service, device_repo, registry, scheduler
    ):
        """重建时 driver.start() 失败应抛出含原因的 ValueError，而非永久卡死"""
        drv = _make_mock_driver(start_side_effect=ConnectionError("PLC unreachable"))
        driver_cls = MagicMock(return_value=drv)
        registry.get_driver_class = MagicMock(return_value=driver_cls)
        device_repo.get = AsyncMock(
            return_value={
                "device_id": "pf-mc",
                "protocol": "mitsubishi_mc",
                "config": {},
                "points": [],
                "status": "offline",
            }
        )

        with pytest.raises(ValueError, match="Device driver recreate failed.*PLC unreachable"):
            await device_service.start_collect("pf-mc")

        # 失败的驱动实例必须被停止并清理，不得残留在实例表中
        drv.stop.assert_awaited_once()
        assert "pf-mc" not in device_service._driver_instances
        scheduler.start_collect.assert_not_awaited()

    async def test_raises_when_no_registered_driver_class(self, device_service, device_repo, registry):
        """注册表中无驱动类时保持原语义：Device driver not found"""
        registry.get_driver_class = MagicMock(return_value=None)
        device_repo.get = AsyncMock(
            return_value={
                "device_id": "d1",
                "protocol": "unknown_proto",
                "config": {},
                "points": [],
                "status": "offline",
            }
        )

        with pytest.raises(ValueError, match="Device driver not found: d1"):
            await device_service.start_collect("d1")

    async def test_online_with_alive_driver_skips(self, device_service, device_repo, scheduler):
        """已 online 且驱动实例健在时跳过（原幂等守卫保持不变）"""
        drv = _make_mock_driver()
        device_service._driver_instances["d1"] = drv
        device_repo.get = AsyncMock(
            return_value={"device_id": "d1", "protocol": "modbus_tcp", "config": {}, "points": [], "status": "online"}
        )

        ok = await device_service.start_collect("d1")

        assert ok is True
        scheduler.start_collect.assert_not_awaited()

    async def test_zombie_online_without_driver_triggers_recreate(
        self, device_service, device_repo, scheduler, registry
    ):
        """状态 online 但驱动实例缺失（僵尸状态）也必须重建，而非被幂等守卫放行"""
        drv = _make_mock_driver()
        driver_cls = MagicMock(return_value=drv)
        registry.get_driver_class = MagicMock(return_value=driver_cls)
        device_repo.get = AsyncMock(
            return_value={"device_id": "d2", "protocol": "modbus_tcp", "config": {}, "points": [], "status": "online"}
        )

        ok = await device_service.start_collect("d2")

        assert ok is True
        drv.start.assert_awaited_once()
        scheduler.start_collect.assert_awaited_once()

    async def test_recreate_simulator_uses_shared_instance(
        self, device_service, device_repo, scheduler, mock_simulator, registry
    ):
        """simulator 协议重建应复用共享模拟器实例并按三参注册点位"""
        device_service._simulator_driver = mock_simulator
        registry.get_driver_class = MagicMock(return_value=MagicMock())  # 模拟器已在注册表注册
        device_repo.get = AsyncMock(
            return_value={
                "device_id": "sim1",
                "protocol": "simulator",
                "config": {},
                "points": [{"name": "t1"}],
                "status": "offline",
            }
        )

        ok = await device_service.start_collect("sim1")

        assert ok is True
        mock_simulator.add_device.assert_awaited_once_with("sim1", {}, [{"name": "t1"}])
        assert device_service._driver_instances["sim1"] is mock_simulator
        scheduler.start_collect.assert_awaited_once()


# ───────────────────────── FIXED-ROBUST-02: load_existing 模拟器参数 ─────────────────────────


class TestLoadExistingSimulatorAddDevice:
    """load_existing_devices 模拟器 add_device 三参调用修复"""

    async def test_simulator_points_registered_not_misrouted_to_config(
        self, device_service, device_repo, registry, scheduler, mock_simulator
    ):
        """重启恢复时模拟器设备的 points 必须传给 points 形参（原实现误传为 config）"""
        device_service._simulator_driver = mock_simulator
        registry.get_driver_class = MagicMock(return_value=MagicMock())
        device_repo.list_all = AsyncMock(
            return_value=(
                [
                    {
                        "device_id": "csv-dev-1",
                        "protocol": "simulator",
                        "config": {"timeout": 5.0},
                        "points": [{"name": "p1", "min": 0, "max": 10}],
                        "collect_interval": 5,
                    }
                ],
                1,
            )
        )

        await device_service.load_existing_devices()

        mock_simulator.add_device.assert_awaited_once_with(
            "csv-dev-1", {"timeout": 5.0}, [{"name": "p1", "min": 0, "max": 10}]
        )
        assert device_service._driver_instances["csv-dev-1"] is mock_simulator
        scheduler.start_collect.assert_awaited_once()


# ───────────────────────── FIXED-ROBUST-03: FINS _is_bit_access ─────────────────────────


class TestFinsIsBitAccess:
    """FINS 驱动 _is_bit_access 静态方法"""

    @pytest.mark.parametrize("dt", ["b", "b0", "b7", "b15"])
    def test_bit_types(self, dt):
        from edgelite.drivers.fins import OmronFinsDriver

        assert OmronFinsDriver._is_bit_access(dt) is True

    @pytest.mark.parametrize("dt", ["w", "i", "ui", "dw", "long", "float", "r", "str", "", "bx", "b1x", "1b"])
    def test_non_bit_types(self, dt):
        from edgelite.drivers.fins import OmronFinsDriver

        assert OmronFinsDriver._is_bit_access(dt) is False

    def test_non_string_input(self):
        from edgelite.drivers.fins import OmronFinsDriver

        assert OmronFinsDriver._is_bit_access(None) is False
        assert OmronFinsDriver._is_bit_access(7) is False

    def test_method_exists_on_driver(self):
        """回归守卫：_read_point_direct_mode 依赖的方法必须真实存在"""
        from edgelite.drivers.fins import OmronFinsDriver

        assert hasattr(OmronFinsDriver, "_is_bit_access")

    def test_decode_matches_bN_types(self):
        """FIXED-ROBUST-03: 响应解码与位写分支必须用 _is_bit_access 匹配 bN，
        否则 D20.5 语法产生的 \"b1\"-\"b15\" 会被误走字解码/字写（整字覆盖）分支"""
        from pathlib import Path

        import edgelite.drivers.fins as fins_mod

        source = Path(fins_mod.__file__).read_text(encoding="utf-8")
        code = "\n".join(ln for ln in source.splitlines() if not ln.lstrip().startswith("#"))
        # 响应解码/位写/校验处必须用 _is_bit_access 匹配 bN；
        # 代码中仅允许保留非 direct 模式委托分支的 1 处精确 "b" 匹配
        assert code.count('data_type == "b"') == 1
        assert code.count('elif data_type == "b"') == 0

    def test_write_direct_mode_bN_uses_bit_offset_frame(self):
        """位写必须使用 word(2B)+bit(1B) 偏移与位区码，不得整字覆盖"""
        import struct

        from edgelite.drivers import fins as fins_mod

        driver = fins_mod.OmronFinsDriver.__new__(fins_mod.OmronFinsDriver)
        driver._dest_node = 1
        driver._unit_no = 0
        driver._source_node = 1
        captured = {}

        async def _fake_request(self, cmd, dt):
            captured["cmd"] = cmd
            captured["dt"] = dt

        with patch.object(fins_mod.OmronFinsDriver, "_fins_tcp_request", _fake_request):
            asyncio.run(fins_mod.OmronFinsDriver._write_point_direct_mode(driver, "d", 20, True, "b5"))

        cmd = captured["cmd"]
        # 帧头 13B + offset 3B + count 2B + data 1B
        assert len(cmd) == 19
        area_code = cmd[12]
        assert area_code == 0x02  # D 位访问区码（0x82 & 0x7F）
        offset_bytes = cmd[13:16]
        assert offset_bytes == bytes([0x00, 0x14, 0x05])  # word=20, bit=5
        assert struct.unpack(">H", cmd[16:18])[0] == 1  # 写 1 字节
        assert cmd[18] == 0x01  # value=True

    def test_validate_write_value_accepts_bN(self):
        from edgelite.drivers.fins import OmronFinsDriver

        ok, _ = OmronFinsDriver._validate_write_value(OmronFinsDriver, 1, "b5")
        assert ok is True
        ok, _ = OmronFinsDriver._validate_write_value(OmronFinsDriver, 2, "b5")
        assert ok is False


# ───────────────────────── FIXED-ROBUST-04: 死代码路径回归守卫 ─────────────────────────


class TestNoRegistryInstanceLookup:
    """api/devices.py 不得再调用 DriverRegistry 上不存在的 get_driver_instance"""

    def test_devices_api_does_not_reference_registry_get_driver_instance(self):
        """回归守卫：DriverRegistry 只维护驱动类不维护实例，
        曾有端点误调用 registry.get_driver_instance 导致写策略与 /metrics 恒为死代码。
        若需要驱动实例，应使用 DeviceService.get_driver_instance。"""
        from pathlib import Path

        import edgelite.api.devices as devices_mod

        source = Path(devices_mod.__file__).read_text(encoding="utf-8")
        # 仅检查代码行（剥离注释行），避免修复说明注释误报
        code_lines = [ln for ln in source.splitlines() if not ln.lstrip().startswith("#")]
        code = "\n".join(code_lines)
        assert "registry.get_driver_instance" not in code
        assert "await svc.get_driver_instance(device_id)" in code  # 实例获取必须经由 DeviceService

    async def test_get_driver_instance_returns_registered_instance(self, device_service):
        """DeviceService.get_driver_instance 是驱动实例的唯一下发通道"""
        drv = MagicMock()
        device_service._driver_instances["d1"] = drv
        assert await device_service.get_driver_instance("d1") is drv
