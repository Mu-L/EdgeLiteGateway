# EdgeLite v1.0-Community × ProtoForge 生产级联调验收报告

- **日期**: 2026-09-23
- **被测件**: EdgeLite v1.0 Community（`EdgeLite-v1.0-Community`，以 `.venv-ci` 可编辑安装运行，端口 8180）
- **测试台架**: ProtoForge（`E:\硕腾网络\PyGBSentry\ProtoForge`，端口 8000，26/27 协议模拟器运行）
- **验收脚本**: `scripts/joint_acceptance.py`（可重复执行，凭据走环境变量，失败退出码 1）
- **机器可读结果**: `docs/acceptance/joint_acceptance_report.json`

---

## 1. 验收结论

**通过。** 三阶段验收 12/12 项全部通过，34 分钟 Soak 采集成功率 99.98%，
全量回归 8189 通过（14 个失败全部定位并修复/归因，详见 §5）。

| 阶段 | 内容 | 结果 |
|---|---|---|
| A 采集一致性 | ProtoForge 源端写入特征值 → EdgeLite 采集比对（modbus/s7/mc/fins/ab/mqtt） | **6/6 PASS** |
| B 下写链路 | EdgeLite API 下写 → 独立第三方协议客户端直读设备线上内存验证 | **5/5 PASS** |
| C 故障注入 | 停止 ProtoForge MC 协议 → EdgeLite 感知（连续失败计数）→ 重启后自动恢复采集 | **PASS** |
| Soak 稳定性 | 34 分钟持续采集，16 台设备 | 33,931 次采集，6 次超时，**99.98%** |
| 回归测试 | `pytest tests/`（EdgeLite 全量） | 8189 passed / 283 skipped / 14 failed（全部归因，见 §5） |
| 前端真实巡检 | 真实浏览器登录 + 逐页巡检（修复上次假阳性） | 核心页面全部渲染真实数据，2 个已知占位页 |

## 2. 联调方法要点

1. **独立线上客户端验证**：阶段 B 不使用 ProtoForge REST 点位接口做验证（其注册表与线上
   协议内存可能不同步，会制造假阳性/假阴性），改用 pymodbus / python-snap7 / pymcprotocol /
   pylogix / FINS 裸帧客户端直读设备内存。
2. **自描述负载归位**：MQTT 验收利用 ProtoForge 发布的自描述 JSON（device_id/point/value）
   校验端到端主题→测点映射。
3. **故障恢复采用轮询窗口**：熔断器半开探测 + 退避重连需 1-2 分钟量级（属合理生产行为），
   验收轮询上限 120s。

## 3. 本次修复缺陷清单

### 3.1 ProtoForge（测试台架，2 项）

| # | 缺陷 | 根因 | 修复 |
|---|---|---|---|
| P1 | MC 线上读写与点位注册表完全脱节；EdgeLite 经 MC 采集恒为 0；iQ-R 帧位读报错 | SLMP 设备字段按"码在前+号在后"解析（实际为号 3B LE + 码 1B；iQ-R 为号 4B + 码 2B）；位子命令 0x0003 未支持 | `protocols/mc/server.py`：新增 `_parse_device_field` 双布局解析、位内存半字节布局、批量/随机读写处理器重写 |
| P2 | MQTT 设备推送后 EdgeLite 侧订阅永远收不到数据 | 推送模板 `subscribe_topic` 默认 `protoforge/data`，与发布模式 `{prefix}/{device}/{point}` 永不匹配 | `integrations/edgelite.py`：默认改为 `{topic_prefix}/#` |

### 3.2 EdgeLite（9 项）

| # | 缺陷 | 影响 | 修复位置 |
|---|---|---|---|
| E1 | MC 驱动写路径缺"点名→地址"映射 | 写任意 name≠address 点位恒 400 | `drivers/mc.py` |
| E2 | S7 驱动写路径缺同名址映射 | 写非 DB 前缀命名的点位恒 400 | `drivers/s7.py` |
| E3 | FINS 驱动写路径缺同名址映射 | 写入错误内存区或被拒 | `drivers/fins.py` |
| E4 | FINS direct 模式字地址按 24 位大端编码 | D10 被读/写成"D0 的 bit10"，采集值静默错误 | `drivers/fins.py`（读+写） |
| E5 | FINS 写帧 count 字段填字节数（应为字数） | 驱动报成功但设备内存未变（静默失败） | `drivers/fins.py` |
| E6 | FINS/TCP 事务无串行化 + 库单次 recv 分帧残留字节 | 字节流错位死循环（Invalid FINS header）与静默脏数据（把帧头节点地址当采集值） | `drivers/fins.py`：事务锁 + 连接后排空 + 错位即断链重建 |
| E7 | FINS direct 帧 ICF=0x00（无需响应位） | 真实 PLC 不回包（台架宽松未暴露） | `drivers/fins.py`：改 0x80 |
| E8 | MQTT 驱动回退匹配不支持通配符 | `protoforge/#` 等通配订阅消息全部静默丢弃 | `drivers/mqtt_client.py`：通配匹配 + 自描述负载归位 |
| E9 | 会话撤销 INSERT 缺 created_at | alembic 表 NOT NULL 无默认 → 并发登录控制静默失效 | `security/session_manager.py` |

### 3.3 健壮性/可观测性增强（EdgeLite）

| # | 增强 | 位置 |
|---|---|---|
| R1 | 采集缓存携带真实采集时间，超期（3×间隔）降级为 uncertain——杜绝"采集停摆仍显示实时数据" | `engine/scheduler.py` + `services/device_service.py` |
| R2 | 启动时驱动恢复失败的设备状态落为 offline（原为无驱动僵尸在线） | `services/device_service.py` |
| R3 | 北向 MQTT 转发器状态接口暴露连接健康（connected/consecutive_failures） | `engine/mqtt_forwarder.py` |
| R4 | FINS 写响应（无数据段）不再被误判为截断 | `drivers/fins.py` |

## 4. 前端真实浏览器巡检（修复上次假阳性）

上次会话的 Playwright 巡检实际全部停留在登录页（24 条路由"OK"为假阳性）。本次用真实
浏览器完成登录后逐页巡检：

- **完全可用**：仪表盘（16 设备在线、AI 推理统计、CPU/内存）、设备管理（列表 + WebSocket
  实时刷新）、设备详情（pf-modbus 全部页签）、规则管理、告警中心、数据查询、系统管理、
  驱动配置、用户管理。
- **已知占位页**：`/observability/*`、`/system/config` 等显示"该功能尚未就绪"——与
  `ACCEPTANCE_GATE_REPORT.md` 记录的约 40 个占位页一致，属已知范围，不阻塞本次验收。

## 5. 回归测试归因

全量 `pytest tests/`（8189 passed / 283 skipped / 14 failed）中 14 个失败全部归因：

| 失败 | 归因 | 处置 |
|---|---|---|
| `test_fins_ext.py` × 11 | 测试工厂 `__new__` 绕过 `__init__`，缺新增 `_fins_txn_lock` 属性 | 已补工厂属性，`test_fins_ext.py` 202/202 通过 |
| `test_device_service.py::TestReadPoints` × 2 | 新鲜度代码遇 MagicMock 调度器缺类型防御 | 已加固（显式类型校验），`test_device_service.py` 55/55 通过 |
| `test_perf1_05_health_check_latency` | 健康检查 53.4ms > 50ms 预算——多进程满载抖动 | 隔离复跑 5/5 通过 |

ProtoForge 侧：协议相关子集 86 passed；`test_edgelite_config_has_correct_register_types`
断言停留在历史缺陷行为（裸地址"4"），已随前缀化修复更新为 `C4`/`HR10`，单测通过。
`test_real_machine_joint` 报错为环境问题：其以 ProtoForge venv 解释器启动 EdgeLite 子进程，
该 venv 缺 `influxdb_client`——非产品缺陷，运行该用例前需补装依赖。

## 6. 已知限制与后续建议

1. **单会话登录策略与自动化测试冲突**：并发登录控制会顶掉浏览器会话；自动化验收应使用
   独立非 admin 账号。
2. **Modbus IR 点位下写映射**：对 IR（输入寄存器）点位的写会落到同号保持寄存器（驱动兼容
   行为）。建议产品层面明确：对只读区点位提供写失败语义或文档化该映射。
3. **占位页**：约 40 个前端占位页待实现（已有报告跟踪）。
4. **ProtoForge 台架**：MC ASCII 帧解析未随本次二进制帧修复同步；随机读 count 字段宽度按
   既有实现保留。联调主路径（二进制 3E/Q + iQ-R）已全覆盖。
5. **全量覆盖率门禁**：CI 门禁 58% 与 pyproject 80% 的双标仍在（本次改动相关模块测试已
   100% 通过），建议按模块逐步补齐核心驱动测试。

## 7. 验收产物

- `scripts/joint_acceptance.py` — 可重复验收脚本
- `docs/acceptance/joint_acceptance_report.json` — 12/12 通过的机器可读结果
- 本报告
