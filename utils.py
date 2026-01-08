#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import psutil


def run_powershell_command(command, capture_output=True):
    """运行PowerShell命令并进行错误监测"""
    cmd = ["powershell.exe", "-Command", command]
    try:
        info(f"执行命令: {command}")
        result = subprocess.run(cmd, capture_output=capture_output, check=True, text=True)
    except subprocess.CalledProcessError as e:
        result = None
        warning(f"执行错误：{e.stderr}")
        warning("是否继续？(y/n)")
        if input().lower() != "y":
            error("用户取消操作")
    return result


def kill_processes_using_files(file_pattern):
    """查找并强行终止占用指定文件模式的进程"""
    info(f"正在扫描占用 {file_pattern} 的进程...")
    target_paths = []
    result = run_powershell_command(
        f"Get-ChildItem -Path '{file_pattern}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName",
        capture_output=True
    )
    if result and result.stdout.strip():
        target_paths = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]

    killed_pids = set()
    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
        try:
            open_files = proc.info['open_files'] or []
            for file in open_files:
                if any(file.path == path for path in target_paths):
                    pid = proc.info['pid']
                    if pid not in killed_pids:
                        warning(f"发现占用进程: {proc.info['name']} (PID {pid})")
                        proc.kill()
                        killed_pids.add(pid)
                        info(f"已终止进程 {proc.info['name']} (PID {pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed_pids:
        info(f"共终止 {len(killed_pids)} 个进程")
    else:
        info("未找到明显占用字体文件的进程")


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        result = run_powershell_command(
            "([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)",
            capture_output=True,
        )
        return result.stdout.strip().lower() == "true"
    except:
        error("检查管理员权限时出错")


def run_as_admin():
    """以管理员权限重新运行脚本"""
    script = os.path.abspath(sys.argv[0])
    powershell_command = f"Start-Process -FilePath '{sys.executable}' -ArgumentList '{script}' -Verb RunAs"
    run_powershell_command(powershell_command)
    sys.exit()


def info(message):
    """显示信息"""
    print(f"\033[94m{message}\033[0m")


def warning(message):
    """显示警告信息"""
    print(f"\033[93m{message}\033[0m", file=sys.stderr)


def error(message):
    """显示错误信息"""
    print(f"\033[91m{message}\033[0m", file=sys.stderr)
    input("按任意键退出...")
    sys.exit(1)


def take_ownership(file_pattern):
    """获取文件所有权"""
    run_powershell_command(f'takeown /F {file_pattern} /A')
    run_powershell_command(f'icacls {file_pattern} /grant Administrators:F')


def restore_ownership(file_pattern, backup_dir):
    """恢复文件所有权和权限"""
    run_powershell_command(f'takeown /F {file_pattern} /A')
    run_powershell_command(f'icacls {file_pattern} /grant Administrators:F')
    run_powershell_command(f'icacls {file_pattern} /C /setowner "NT SERVICE\\TrustedInstaller"')
    acl_file = os.path.join(backup_dir, "acl")
    if os.path.exists(acl_file):
        run_powershell_command(f'icacls C:\\windows\\Fonts\\ /C /restore "{acl_file}"')


def delete_font_files(file_pattern):
    """删除字体文件"""
    run_powershell_command(f'Remove-Item -Path {file_pattern} -Force -Recurse')


def copy_font_files(src_dir, dst_dir, files):
    """复制字体文件"""
    for file in files:
        src = os.path.join(src_dir, file)
        dst = os.path.join(dst_dir, file)
        if os.path.exists(src):
            shutil.copy2(src, dst)


def logoff_system():
    """注销系统"""
    warning("点击任意键注销系统")
    input()
    run_powershell_command("shutdown -L")


def load_plugin(font_name):
    """加载字体处理插件"""
    font_name_lower = font_name.lower()
    try:
        from plugins import msyh
        if font_name_lower == "msyh":
            return msyh.MSYHPlugin()
    except ImportError:
        pass
    error(f"未找到字体 '{font_name}' 的插件")
