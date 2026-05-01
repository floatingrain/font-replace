# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Windows 系统字体替换工具。通过操作字体名称表、文件系统和 Windows 注册表，将系统内置字体（如微软雅黑、Segoe UI 等）替换为用户指定的字体。仅限 Windows 平台，需要管理员权限。

## 常用命令

```bash
# 安装依赖
uv sync

# 运行（需要管理员权限）
python main.py --config config/config.json

# 构建独立可执行文件
uv run pyinstaller main.spec --clean
# 输出：dist/font-replace.exe
```

项目未配置测试和代码检查工具。

## 架构

三层设计，采用模板方法模式：

- **`main.py`** — CLI 入口：参数解析 → 管理员检查 → 加载配置 → 运行转换器 → 提示注销
- **`config/loader.py`** — 数据类层级：`Config` → `ConverterConfig`（type: "ttc"/"ttf"）→ `MapperConfig`（源文件、替换文件、输出文件、注册表项、备份目录）
- **`converters/`** — `BaseConverter` 定义处理流水线：`backup_and_prepare()` → `convert()` → `install()`。子类 `TTCConverter` 和 `TTFConverter` 实现 `convert()` 和 `prepare_resource()`。
- **`utils/common.py`** — 系统操作：PowerShell 子进程、管理员检查、进程终止（psutil）、文件所有权管理（takeown/icacls）、彩色日志输出
- **`utils/font.py`** — 字体操作（基于 fonttools）：`otc2otf`/`otf2otc`（TTC 解包/打包）、`ttx_extract_name`/`ttx_merge`（名称表提取/合并）

核心机制：提取原字体的 `name` 表（元数据），合并到替换字体中，然后替换系统字体文件和注册表项。这样 Windows 会将替换字体识别为原字体。

## 关键约束

- 需要 Python >= 3.14（在 `.python-version` 中固定）
- 包管理器为 **uv**（非 pip/pipenv）
- 必须以管理员身份运行 — 涉及修改 `C:\Windows\Fonts`、注册表和文件所有权
- 无自动恢复/撤销机制 — 会创建备份，但需要手动恢复
- 依赖中的 `pyinstaller` 和 `afdko` 为直接依赖；许多字体相关包是 `fonttools` 的传递依赖
