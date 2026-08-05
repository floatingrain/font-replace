# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Windows 字体转换工具。提取原字体的 `name` 表（元数据），合并到用户指定的替换字体中，输出与原字体同名的字体文件至 `target-fonts/` 目录。本工具**不再**修改系统目录、注册表或文件所有权，不再需要管理员权限。

## 常用命令

```bash
# 安装依赖
uv sync

# 转换字体
python main.py convert -c config/config.json

# 构建独立可执行文件
uv run pyinstaller main.spec --clean
# 输出：dist/font-replace.exe
```

项目未配置测试和代码检查工具。

## 架构

模板方法模式，三层结构：

- **`main.py`** — CLI 入口（argparse 子命令 `convert`，`-c` 指定配置文件路径，必需）→ 加载配置 → 资源校验 → 运行编排器。
- **`config/loader.py`** — 数据类层级：`Config` → `ConverterConfig`（type: "ttc"/"ttf"）→ `MapperConfig`（仅 `source_file`、`fake_file`）。`resource_check()` 校验 `source_file` 与 `fake_file` 是否存在。
- **`converter/`** — `base.py` 中的 `BaseConverter` 定义流水线：为每个 mapper 创建临时工作目录（`tempfile.TemporaryDirectory`），调用 `convert_mapper()`。子类 `TTCConverter`（`ttc.py`）和 `TTFConverter`（`ttf.py`）在该工作目录中处理。`orchestrator.py` 中的 `run_convert()` 通过 `CONVERTER_REGISTRY`（在 `__init__.py` 中维护）按 converter type 查找并执行对应转换器。
- **`utils/`** — `font.py`：基于 fontTools 的字体操作（otc2otf/otf2otc 打包解包、ttx_extract_name/ttx_merge 名称表提取合并）。

核心机制：提取 `source_file` 的 `name` 表（元数据），合并到 `fake_file` 中，输出到 `target-fonts/` 目录。

## 关键约束

- Python >= 3.14（`.python-version` 固定）
- 包管理器为 **uv**（非 pip/pipenv）
- **不需要管理员权限** — 仅读写当前工作目录下的临时目录和 `target-fonts/`，不修改 `C:\Windows\Fonts`、注册表或文件所有权
- 配置文件不在仓库中，需用户手动创建并通过 `-c` 参数指定（参考 `config-example.json` 和 `yahei&segoe.json`）
- 每个 mapper 在独立的临时目录中处理，结束后自动清理
