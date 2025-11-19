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
    # 将通配符模式转换为绝对路径列表
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
        # 使用PowerShell检查管理员权限
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


def delete_registry_entries():
    """删除注册表项"""
    warning("正在删除注册表项...")

    # 删除注册表项
    run_powershell_command(
        R"Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name 'Microsoft Yahei & Microsoft Yahei UI (TrueType)' -Force -ErrorAction SilentlyContinue"
    )
    run_powershell_command(
        R"Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name 'Microsoft Yahei Bold & Microsoft Yahei UI Bold (TrueType)' -Force -ErrorAction SilentlyContinue"
    )
    run_powershell_command(
        R"Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name 'Microsoft Yahei Light & Microsoft Yahei UI Light (TrueType)' -Force -ErrorAction SilentlyContinue"
    )


def restore_files(rootdir):
    """从备份恢复字体文件"""
    backup_dir = os.path.join(rootdir, "msyh-backup")

    # 检查备份目录是否存在
    if not os.path.exists(backup_dir):
        error("备份目录不存在！")

    os.chdir(backup_dir)

    # 检查备份的字体文件是否存在
    required_files = ["msyh.ttc.bak", "msyhl.ttc.bak", "msyhbd.ttc.bak"]
    for file in required_files:
        if not os.path.exists(os.path.join(backup_dir, file)):
            # 检查不带.bak扩展名的文件
            base_file = file.replace(".bak", "")
            if not os.path.exists(os.path.join(backup_dir, base_file)):
                error(f"恢复字体失败: {file} 或 {base_file} 不存在")

    info("正在恢复字体文件...")

    # 获取文件所有权
    run_powershell_command(R"takeown /F C:\Windows\Fonts\msyh* /A")
    run_powershell_command(R"icacls C:\Windows\Fonts\msyh* /grant Administrators:F")

    # 查找并终止占用字体文件的进程
    kill_processes_using_files('C:\\Windows\\Fonts\\msyh*')

    # 尝试删除当前字体文件
    warning("尝试删除当前字体文件...")
    run_powershell_command(
        R"Remove-Item -Path 'C:\Windows\Fonts\msyh*' -Force -Recurse"
    )

    # 最后检查文件是否还存在
    check_command = "Get-ChildItem -Path 'C:\\Windows\\Fonts' -Filter 'msyh*' -ErrorAction SilentlyContinue | Format-Table FullName"
    result = run_powershell_command(check_command)

    if result and result.stdout.strip():
        warning("警告: 仍有字体文件存在:")
        print(result.stdout)
        warning("这些文件将在系统重启后被删除")
    else:
        info("所有字体文件已成功删除")

    # 从备份复制字体文件（考虑.bak扩展名）
    for file in ["msyh.ttc", "msyhl.ttc", "msyhbd.ttc"]:
        bak_file = file + ".bak"
        src = os.path.join(backup_dir, bak_file) if os.path.exists(os.path.join(backup_dir, bak_file)) else os.path.join(backup_dir, file)
        dst = os.path.join(R"C:\Windows\Fonts", file)
        shutil.copy2(src, dst)

    # 恢复权限
    run_powershell_command(R"takeown /F C:\Windows\Fonts\msyh* /A")
    run_powershell_command(R"icacls C:\Windows\Fonts\msyh* /grant Administrators:F")
    run_powershell_command(
        R'icacls C:\windows\Fonts\msyh* /C /setowner "NT SERVICE\TrustedInstaller"'
    )

    # 恢复ACL权限
    acl_file = os.path.join(backup_dir, "acl")
    if os.path.exists(acl_file):
        run_powershell_command(
            f"icacls C:\\windows\\Fonts\\ /C /restore \"{acl_file}\""
        )
    else:
        warning("ACL权限文件不存在，跳过权限恢复")

    # 添加注册表项
    run_powershell_command(
        R"New-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name 'Microsoft Yahei & Microsoft Yahei UI (TrueType)' -Value 'msyh.ttc' -PropertyType String -Force"
    )
    run_powershell_command(
        R"New-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name 'Microsoft Yahei Bold & Microsoft Yahei UI Bold (TrueType)' -Value 'msyhbd.ttc' -PropertyType String -Force"
    )
    run_powershell_command(
        R"New-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name 'Microsoft Yahei Light & Microsoft Yahei UI Light (TrueType)' -Value 'msyhl.ttc' -PropertyType String -Force"
    )

    os.chdir(rootdir)


def main():
    """主函数"""
    # 检查管理员权限
    if not is_admin():
        run_as_admin()

    # 获取脚本所在目录
    rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(rootdir)

    # 检查注册表中是否存在字体项
    result = run_powershell_command(
        R"Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'; if ($?) { Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name 'Microsoft Yahei & Microsoft Yahei UI (TrueType)' }",
        capture_output=True,
    )
    
    has_registry_entry = False
    if result and "Microsoft YaHei & Microsoft YaHei UI (TrueType)" in result.stdout:
        has_registry_entry = True

    try:
        if has_registry_entry:
            # 如果注册表项存在，则删除它
            delete_registry_entries()
        else:
            # 否则直接恢复字体文件
            restore_files(rootdir)

        # 提示用户注销
        warning("点击任意键注销系统")
        input()

        # 注销系统
        run_powershell_command("shutdown -L")

    except Exception as e:
        error(f"发生错误: {str(e)}")


if __name__ == "__main__":
    main()
