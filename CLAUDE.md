# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Windows 系统字体替换工具。通过操作字体名称表、文件系统和 Windows 注册表，将系统内置字体（如微软雅黑、Segoe UI 等）替换为用户指定的字体。仅限 Windows 平台，需要管理员权限。

## 常用命令

```bash
# 安装依赖
uv sync

# 替换字体（需要管理员权限）
python main.py replace -c config/config.json

# 从备份还原字体（需要管理员权限，当前未实现）
python main.py restore -c config/config.json

# 构建独立可执行文件
uv run pyinstaller main.spec --clean
# 输出：dist/font-replace.exe
```

项目未配置测试和代码检查工具。

## 架构

模板方法模式，四层结构：

- **`main.py`** — CLI 入口（argparse 子命令 `replace`/`restore`，均需 `-c` 指定配置文件路径）→ 管理员检查 → 加载配置 → 资源校验 → 运行编排器 → 提示重启
- **`config/loader.py`** — 数据类层级：`Config` → `ConverterConfig`（type: "ttc"/"ttf"）→ `MapperConfig`（source_file、fake_file、registry_entry、font_name_display、backup_dir）。`resource_check()` 和 `restore_resource_check()` 分别校验替换和还原的前置条件。注意：`MapperConfig.from_dict()` 自动生成 `backup_dir="backup/{font_name_display}"`，每个字体独立备份目录。
- **`replacer/`** — `base.py` 中的 `BaseConverter` 定义流水线：`backup_and_prepare()` → `convert()` → `install()`。子类 `TTCConverter`（`ttc.py`）和 `TTFConverter`（`ttf.py`）实现抽象方法 `prepare_resource()`、`convert()`、`add_registry_entries()`。`replace.py` 中的 `run_replace()` 按 converter type 实例化对应转换器并执行。
- **`restorer/restore.py`** — 还原编排器，当前整个文件已注释掉，`main.py` 中也注释了相关导入。还原功能暂未实现。
- **`utils/`** — `common.py`：PowerShell 子进程（`run_powershell_command`）、管理员检查（`is_admin`）、进程终止（`kill_processes_using_files`，基于 psutil）、文件所有权管理（`take_ownership`/`restore_ownership`，通过 takeown/icacls）。`font.py`：基于 fonttools 的字体操作（otc2otf/otf2otc 打包解包、ttx_extract_name/ttx_merge 名称表提取合并）。

核心机制：提取原字体的 `name` 表（元数据），合并到替换字体中，使 Windows 将替换字体识别为原字体。

## 关键约束

- Python >= 3.14（`.python-version` 固定）
- 包管理器为 **uv**（非 pip/pipenv）
- 必须以管理员身份运行 — 修改 `C:\Windows\Fonts`、注册表（`HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts`）和文件所有权
- 还原功能依赖 `backup_dir` 中的备份文件，无备份则无法还原
- 配置文件不在仓库中，需用户手动创建并通过 `-c` 参数指定（参考 `config-example.json` 和 `yahei&segoe.json`）
- 字体替换时会强制终止占用目标文件的进程（`kill_processes_using_files`），替换完成后自动恢复文件 ACL 权限并交还 TrustedInstaller 所有权
