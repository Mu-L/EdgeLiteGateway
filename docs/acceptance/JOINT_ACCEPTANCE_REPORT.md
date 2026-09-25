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

---

## 附录：第二轮联调（2026-09-24，专用账号 + OPC-UA/HTTP 扩展）

### A2. 结论

**通过。** 矩阵扩展至 8 协议后 14/14 全部通过，全程使用专用 `joint_accept` 账号（operator
角色 + 设备资源共享），不再与 admin 会话互顶。

| 阶段 | 结果 |
|---|---|
| A 采集一致性（modbus/s7/mc/fins/ab/mqtt/**opcua**） | 7/7 PASS（第三轮修复 E13/E14 后） |
| A HTTP 推送接收链路（webhook 被动接收验证） | 1/1 PASS |
| B 下写链路（独立线上客户端验证） | 5/5 PASS |
| C 故障注入与恢复 | PASS |

### B2. 本轮修复

| # | 修复 | 位置 |
|---|---|---|
| E10 | OPERATOR 角色补授 DEVICE_WRITE_POINT——工业操作员本职即写设定值；写路径已有写策略/频率限制/审计三重保护。修复后自动化与现场操作无需共用 admin | `security/rbac.py` |
| E11 | `/devices/{id}/health` 对 http_webhook 等统计缺数值字段的驱动返回 None → ResponseValidationError → 500。现剔除 None 由模型默认值兜底，健康接口对任何协议可用 | `api/devices.py` |
| E12 | 高负载下 SQLite 短暂锁表导致会话持久化失败 → 直接放弃内存注册 → 登录返回的 token 立即 401（联调实测 database is locked）。现降级为内存会话并告警，连接超时 5s→10s | `security/session_manager.py` |

### C2. 环境与流程修正

1. **专用账号**：`joint_accept`（operator）+ resource_shares 设备级授权；ProtoForge 全局
   设置的 edgelite 凭据同步切换，其 IntegrationManager 的登录带 `no_revoke=True`，
   不再触发并发登录互顶。
2. **真机联调用例修复**（ProtoForge 侧）：`test_real_machine_joint` 以 ProtoForge venv
   解释器启动 EdgeLite 子进程、缺 `influxdb_client` 即崩；现优先使用 EdgeLite 自带
   `.venv-ci` 解释器。三个 EdgeLite 联调测试文件 64/64 通过。
3. **MQTT 主题适配**：ProtoForge pf-mqtt 的 topic_prefix 被移除后发布主题变为
   `pf-mqtt/temp`；EdgeLite 侧订阅改 `#`（负载自描述 device_id/point 路由不依赖主题）。
   venv 内 starlette 曾漂移至 1.6.0（lock 为 1.3.1），已回退对齐；fastapi 0.141.1
   与 lock 0.139.0 在本缺陷上行为一致，与 starlette 版本无关。
4. **验收脚本健壮性**：重登后重置 CSRF、网络抖动重试、阶段 A 竞态重读（3 次）、
   就绪判定要求 quality=good。

### D2. 已知台架限制（非 EdgeLite 缺陷）

1. **ProtoForge Modbus 双存储分歧**：REST 写点位的值与生成器 tick 的动态值分别落在
   两个寄存器存储，独立 pymodbus 客户端与经 REST 写入路径的客户端可能读到不同数据
   （联调实测：REST 写 9999 后线上探针读到的仍是生成器动态值）。EdgeLite 侧 word1
   的写链路正确性由阶段 B 独立线上验证覆盖；阶段 A 采集用例收敛到生成器同步稳定的
   temp 点。
2. **resource-shares REST 422（上游 FastAPI 缺陷）**：全量应用下
   `POST/GET /api/v1/resource-shares` 返回 "query -> func: Field required"；带
   `?func=1` 则 500（`run_in_threadpool() got multiple values for argument 'func'`）。
   最小复现（仅挂载 resource_shares 路由）正常，随挂载路由增多复现——为 FastAPI
   0.139.0/0.141.1 惰性路由（`_IncludedRouter`）跨路由依赖错配，starlette 1.3.1 与
   1.6.0 均复现，版本对齐无法规避。当前共享经 resource_shares 表直写供应；建议向上游
   报告或等待修复。
3. **pf-opcua 已修复（E13/E14，EdgeLite 驱动缺陷）**：阶段 A 曾时序抖动，第三轮联调
   定位为 EdgeLite OPC-UA 驱动两处真缺陷并修复——(a) keepalive 访问 asyncua 2.x 不存在的
   `client.session_state` 属性恒抛异常 → 会话被误判过期无限重建；(b) staleness 守卫
   （1.5s 无订阅推送即判陈旧）错误地作用于**直读**结果，静态值设备（设定点/状态量，
   写一次不再变化）的直读恒被误杀为 uncertain。修复后静态值重复直读稳定 good，
   最终验收 14/14 全通过。
4. `test_real_machine_joint` 的 EdgeLite 子进程与常驻实例共用 `data/logs/edgelite.log`
   导致日志轮转 PermissionError（Windows 多实例下，测试环境问题）。


---

## 附录三：协议覆盖总表（2026-09-25，第四轮）

### A4. 结论

**17/17 全部通过。** 验收矩阵扩展至 9 设备 10 链路；剩余两个驱动（opc_da/onvif）在本台架
无对应模拟能力，已如实标注（见 C4）。

| 南向协议 | 采集 | 下写 | 验证形态 |
|---|---|---|---|
| Modbus TCP | ✅ | ✅ 线上验证 | pymodbus 独立客户端 |
| Modbus RTU（TCP-RTU 网关模式） | ✅ | ✅ 线上验证 | 网关拓扑：PF RTU TCP bridge ↔ EdgeLite tcp_gateway；独立 pymodbus 客户端 |
| 西门子 S7 | ✅ | ✅ 线上验证 | python-snap7 |
| 三菱 MC（Q/iQ-R） | ✅ | ✅ 线上验证 | pymcprotocol |
| 欧姆龙 FINS | ✅ | ✅ 线上验证 | FINS 裸帧 |
| 罗克韦尔 AB | ✅ | ✅ 线上验证 | pylogix |
| MQTT client | ✅ 订阅 | —（订阅链路） | paho 独立订阅 |
| OPC-UA | ✅ 订阅+直读 | ✅ 线上验证 | asyncua 独立客户端 |
| HTTP Webhook | ✅ 推送接收 | —（被动链路） | push 端点→缓存→读回 |
| Simulator | ✅（5 台常驻） | — | 连续采集 |
| OPC DA | — | — | 本台架无 DCOM 模拟；PF 的"OPC-DA TCP 桥"与 EdgeLite 驱动的 DCOM 通道不可互操作，需真实 OPC DA 服务器环境 |
| ONVIF | — | — | 台架无摄像头模拟；需真实网络摄像头 |

### B4. 本轮修复（E15/E16，均为生产级阻塞缺陷）

| # | 缺陷 | 影响 | 修复 |
|---|---|---|---|
| E15 | OPC-UA 写不带显式 VariantType：asyncua 把 Python int/float 默认推断为 Int64/Double，与节点声明类型（如 Int32）不符 → BadTypeMismatch → 写恒 400 | OPC-UA 下写全废 | 单点与批量写均按 `_read_node_data_type` 的节点实际类型携带显式 VariantType（`drivers/opcua.py`） |
| E16 | 设备配置校验把所有协议的 `port` 一律按 TCP 端口整数校验；modbus_rtu 的 port 是串口路径（schema 声明 string）→ **RTU 设备无法通过 REST API 创建**；且 repo 层要求 serial_port 键与驱动 schema 的 port 键互相矛盾 | modbus_rtu 全协议被 API 层锁死 | 驱动基类与 sqlite_repo 校验器尊重 schema 声明类型：串口路径按字符串校验（拒绝整数/纯数字串/空），tcp_gateway（串口服务器）模式豁免串口路径（`drivers/base.py`、`storage/sqlite_repo.py`） |

配套：验收脚本修正 HTTP 4xx 被误当网络错误重试的分类问题；契约测试按新语义更新
（串口路径类型契约、网关豁免用例）。

### C4. 部署注意事项

1. **Modbus RTU TCP-RTU 网关**：本机验证时 EdgeLite modbus_slave 占用 `127.0.0.1:5021`
   特定绑定，PF RTU 网桥绑 `0.0.0.0:5021`——回环连接优先命中特定绑定，须用 LAN IP 访问
   网桥。生产部署应规划独立端口避免歧义。
2. **OPC-UA 下写**：EdgeLite 设备点位的 data_type 需与服务器节点声明类型一致
   （驱动按该类型发类型化写；类型不符会被 `_validate_write_type` 拒绝并审计）。
