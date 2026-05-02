#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys

from config.loader import load_config, resource_check, restore_resource_check
from replacer.replace import run_replace
from restorer.restore import run_restore
from utils.common import is_admin, run_powershell_command


class _ColorFormatter(logging.Formatter):
    """带 ANSI 颜色的日志格式化器"""

    COLORS = {
        logging.DEBUG: "\033[90m",
        logging.INFO: "\033[94m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[91m",
        logging.CRITICAL: "\033[91m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        color = self.COLORS.get(record.levelno, self.RESET)
        return f"{color}{msg}{self.RESET}"


_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(_ColorFormatter("%(levelname)s: %(message)s"))
_root = logging.getLogger()
_root.setLevel(logging.DEBUG)
_root.addHandler(_handler)
_root.propagate = False


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
        logging.error("当前非管理员权限，无法执行操作。")
        input("按任意键退出...")
        sys.exit(1)

    # 2. 加载配置
    config_path = os.path.abspath(args.config)
    logging.info(f"正在加载配置: {config_path}")
    config = load_config(config_path)

    # 3. 进行前置检查
    if config is None:
        logging.error("配置加载失败，无法继续执行。")
        input("按任意键退出...")
        sys.exit(1)

    if args.command == "replace":
        logging.info("正在检查配置资源...")
        if not resource_check(config):
            logging.error("前置资源配置检查未通过，请修正配置后重试。")
            input("按任意键退出...")
            sys.exit(1)
    elif args.command == "restore":
        logging.info("正在检查备份资源...")
        if not restore_resource_check(config):
            logging.error("备份完整性检查未通过，无法执行恢复。")
            input("按任意键退出...")
            sys.exit(1)

    # 4. 执行子命令
    if args.command == "replace":
        run_replace(config)
    elif args.command == "restore":
        run_restore(config)

    # 5. 提示重启
    logging.warning("请点击任意键重启系统以使更改生效...")
    input()
    run_powershell_command("shutdown -r")


if __name__ == "__main__":
    main()
