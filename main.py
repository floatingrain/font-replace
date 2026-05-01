#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os

from config.loader import load_config, resource_check, restore_resource_check
from replace.replace import run_replace
from restore.restore import run_restore
from utils.common import error, info, is_admin, run_powershell_command, warning


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="Windows字体替换工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # replace 子命令
    replace_parser = subparsers.add_parser("replace", help="执行字体替换")
    replace_parser.add_argument("-c", "--config", help="配置文件路径")

    # restore 子命令
    restore_parser = subparsers.add_parser("restore", help="从备份恢复原始字体")
    restore_parser.add_argument("-c", "--config", help="配置文件路径")

    args = parser.parse_args()

    # 未指定子命令时显示帮助
    if not args.command:
        parser.print_help()
        return

    # 1. 检查管理员权限
    if not is_admin():
        error("当前非管理员权限，无法执行操作。")
        return

    # 2. 加载配置
    config_path = os.path.abspath(args.config)
    info(f"正在加载配置: {config_path}")
    config = load_config(config_path)

    # 3. 进行前置检查
    if config is None:
        error("配置加载失败，无法继续执行。")
        return

    if args.command == "replace":
        info("正在检查配置资源...")
        if not resource_check(config):
            error("前置资源配置检查未通过，请修正配置后重试。")
            return
    elif args.command == "restore":
        info("正在检查备份资源...")
        if not restore_resource_check(config):
            error("备份完整性检查未通过，无法执行恢复。")
            return

    # 4. 执行子命令
    if args.command == "replace":
        run_replace(config)
    elif args.command == "restore":
        run_restore(config)

    # 5. 提示重启
    warning("请点击任意键重启系统以使更改生效...")
    input()
    run_powershell_command("shutdown -r")


if __name__ == "__main__":
    main()
