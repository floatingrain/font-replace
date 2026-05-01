#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os

from config.loader import load_config, resource_check
from converters import TTCConverter, TTFConverter
from utils.common import error, info, is_admin, warning


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="Windows字体替换工具")
    parser.add_argument(
        "-c", "--config", default="config/config.json", help="配置文件路径"
    )
    args = parser.parse_args()

    # 1. 检查管理员权限
    if not is_admin():
        error("当前非管理员权限，无法执行操作。")
        return

    # 2. 加载配置
    config_path = os.path.abspath(args.config)
    info(f"正在加载配置: {config_path}")
    config = load_config(config_path)

    # 3. 进行前置检查
    info("正在检查配置资源...")
    if config is None:
        error("配置加载失败，无法继续执行。")
        return
    if not resource_check(config):
        error("前置资源配置检查未通过，请修正配置后重试。")
        return

    # 4. 执行转换
    try:
        for converter_config in config.converters:
            converter_type = converter_config.type.lower()

            if converter_type == "ttc":
                converter = TTCConverter(converter_config)
            elif converter_type == "ttf":
                converter = TTFConverter(converter_config)
            else:
                warning(f"未知的转换器类型: {converter_type}，跳过")
                continue

            converter.run()

        info("所有任务执行完毕！")

        # 5. 提示重启
        warning("请点击任意键重启系统以使更改生效...")
        input()
        from utils.common import run_powershell_command

        run_powershell_command("shutdown -r")

    except Exception as e:
        # 捕获未处理的异常，打印堆栈
        import traceback

        traceback.print_exc()
        error(f"程序执行出错: {e}")


if __name__ == "__main__":
    main()
