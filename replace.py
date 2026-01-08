#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil


def load_plugin(font_name):
    """加载字体处理插件"""
    font_name_lower = font_name.lower()
    try:
        if font_name_lower == "msyh":
            from plugin import msyh
            return msyh.MSYHPlugin()
        elif font_name_lower == "segoevf":
            from plugin import segoevf
            return segoevf.SegoeVFPlugin()
    except ImportError as e:
        error(f"加载插件失败: {e}")
    error(f"未找到字体 '{font_name}' 的插件")


def error(message):
    """显示错误信息"""
    print(f"\033[91m{message}\033[0m", file=sys.stderr)
    input("按任意键退出...")
    sys.exit(1)


def main():
    """主函数"""
    if len(sys.argv) != 2:
        error("用法: python replace.py <字体名称>\n支持的字体: msyh, segoevf")
    
    font_name = sys.argv[1].lower()
    
    from utils import is_admin, run_as_admin, run_powershell_command, logoff_system, info, warning, error
    
    if not is_admin():
        run_as_admin()
    
    rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(rootdir)
    
    plugin = load_plugin(font_name)
    
    result = run_powershell_command(plugin.get_registry_check_query(), capture_output=True)
    if result:
        has_original_fonts = any(entry in result.stdout for entry in plugin.registry_entries)
    else:
        has_original_fonts = False
    
    try:
        if has_original_fonts:
            plugin.backup(rootdir)
            plugin.confirm(rootdir)
            plugin.convert(rootdir)
            plugin.delete_registry()
        else:
            info(f"未发现原始{plugin.font_name_display}字体，跳过备份")
            plugin.replace(rootdir)
        
        logoff_system()
    
    except Exception as e:
        error(f"发生错误: {str(e)}")


if __name__ == "__main__":
    main()
