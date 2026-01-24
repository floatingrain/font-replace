#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from config.loader import load_config
from converters import TTCConverter, TTFConverter
from utils import is_admin, info, error, warning

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="Windows字体替换工具")
    parser.add_argument("-c", "--config", default="config/config.json", help="配置文件路径")
    args = parser.parse_args()

    # 1. 检查管理员权限
    if not is_admin():
        error("当前非管理员权限，无法执行操作。")
        return

    # 2. 加载配置
    config_path = os.path.abspath(args.config)
    info(f"正在加载配置: {config_path}")
    
    if not os.path.exists(config_path):
        # 如果默认配置不存在，检查是否有 example
        example_path = os.path.join(os.path.dirname(config_path), "config-example.json")
        if os.path.exists(example_path) and not os.path.exists(config_path):
            warning(f"配置文件不存在，请参考 {example_path} 创建 {config_path}")
            # 为了演示方便，这里不直接退出，而是提示错误
            error(f"配置文件未找到: {config_path}")
        else:
            error(f"配置文件未找到: {config_path}")

    try:
        config = load_config(config_path)
    except Exception as e:
        error(str(e))

    # 3. 执行转换
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
        
        # 4. 提示注销
        warning("请点击任意键注销系统以使更改生效...")
        input()
        from utils import run_powershell_command
        run_powershell_command("shutdown -L")
        
    except Exception as e:
        # 捕获未处理的异常，打印堆栈
        import traceback
        traceback.print_exc()
        error(f"程序执行出错: {e}")

if __name__ == "__main__":
    main()
