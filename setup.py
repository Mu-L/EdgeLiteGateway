from setuptools import setup

# 说明：早期版本曾通过 Cython 编译 src/edgelite/_cython/*.pyx 加速模块
# （rule_compare / modbus_mapper）。该目录与 .pyx 源码已从仓库移除，
# 纯 Python 实现为唯一实现，故不再声明 ext_modules。
# FIXED(ci): 旧声明导致 build 隔离环境中 cythonize() 抛出
# "'src/edgelite/_cython/rule_compare.pyx' doesn't match any files"，
# 使 python -m build 在 sdist/wheel 阶段直接失败。
setup()
