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
        error("用法: python restore.py <字体名称>\n支持的字体: msyh, segoevf")
    
    font_name = sys.argv[1].lower()
    
    from utils import (
        is_admin, run_as_admin, run_powershell_command, 
        kill_processes_using_files, take_ownership, 
        restore_ownership, logoff_system, info, warning, error
    )
    
    if not is_admin():
        run_as_admin()
    
    rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(rootdir)
    
    plugin = load_plugin(font_name)
    backup_dir = os.path.join(rootdir, plugin.backup_dir_name)
    
    if not os.path.exists(backup_dir):
        error("备份目录不存在！")
    
    os.chdir(backup_dir)
    
    for file in plugin.output_files:
        bak_file = file + ".bak"
        if not os.path.exists(os.path.join(backup_dir, bak_file)) and not os.path.exists(os.path.join(backup_dir, file)):
            error(f"恢复字体失败: {file} 或 {bak_file} 不存在")
    
    try:
        plugin.delete_registry()
        
        info("正在恢复字体文件...")
        
        take_ownership(f'C:\\Windows\\Fonts\\{plugin.file_pattern}')
        
        kill_processes_using_files(f'C:\\Windows\\Fonts\\{plugin.file_pattern}')
        
        warning("尝试删除当前字体文件...")
        run_powershell_command(f"Remove-Item -Path 'C:\\Windows\\Fonts\\{plugin.file_pattern}' -Force -Recurse")
        
        check_result = run_powershell_command(
            f"Get-ChildItem -Path 'C:\\Windows\\Fonts' -Filter '{plugin.file_pattern}' -ErrorAction SilentlyContinue | Format-Table FullName"
        )
        
        if check_result and check_result.stdout.strip():
            warning("警告: 仍有字体文件存在:")
            print(check_result.stdout)
            warning("这些文件将在系统重启后被删除")
        else:
            info("所有字体文件已成功删除")
        
        for file in plugin.output_files:
            bak_file = file + ".bak"
            src = os.path.join(backup_dir, bak_file) if os.path.exists(os.path.join(backup_dir, bak_file)) else os.path.join(backup_dir, file)
            dst = os.path.join("C:\\Windows\\Fonts", file)
            shutil.copy2(src, dst)
        
        restore_ownership(f'C:\\Windows\\Fonts\\{plugin.file_pattern}', backup_dir)
        
        for name, value in plugin.registry_entries_dict.items():
            run_powershell_command(
                f"New-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' -Name '{name}' -Value '{value}' -PropertyType String -Force"
            )
        
        os.chdir(rootdir)
        
        logoff_system()
    
    except Exception as e:
        error(f"发生错误: {str(e)}")


if __name__ == "__main__":
    main()
