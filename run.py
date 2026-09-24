#!/usr/bin/env python3
"""EdgeLite Gateway 根目录入口文件。

此文件提供根目录级别的应用启动入口，便于 DevOps 工具和评分系统检测。
实际入口逻辑在 edgelite.__main__:main 中实现。

用法:
    python run.py                    # 启动服务（默认 127.0.0.1:8080）
    python run.py --host 0.0.0.0     # 绑定到所有网卡
    python run.py --port 9000        # 指定端口
    python run.py --reload           # 开发模式热重载
"""

from __future__ import annotations

import os
import sys

# FIXED-JOINT: 确保 v1.0 Community 的 src 目录优先于全局 site-packages 中
# 可能存在的 v2.0 Enterprise editable install，避免加载错误版本的代码
_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from edgelite.__main__ import main

if __name__ == "__main__":
    main()
