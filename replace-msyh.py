#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
from pathlib import Path
import urllib.request


def run_powershell_command(command, capture_output=True):
    """运行PowerShell命令并进行错误监测"""
    cmd = ["powershell.exe", "-Command", command]
    try:
        info(f"执行命令: {command}")
        result = subprocess.run(
            cmd, capture_output=capture_output, check=True, text=True
        )
    except subprocess.CalledProcessError as e:
        result = None
        warning(f"执行错误：{e.stderr}")
        warning("是否继续？(y/n)")
        if input().lower() != "y":
            error("用户取消操作")
    return result


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


def backup(rootdir):
    """备份原有字体"""
    backup_dir = os.path.join(rootdir, "msyh-backup")
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    os.makedirs(backup_dir)
    info("正在备份微软雅黑字体...")
    # 保存ACL权限
    run_powershell_command(
        f"icacls C:\\Windows\\Fonts\\msyh* /save '{os.path.join(backup_dir, "acl")}' /T"
    )
    # 复制字体文件
    for file in os.listdir("C:\\Windows\\Fonts"):
        if file.startswith("msyh"):
            src = os.path.join("C:\\Windows\\Fonts", file)
            dst = os.path.join(backup_dir, file)
            shutil.copy2(src, dst)
    # 使用otc2otf和ttx工具处理字体
    # 注意：这里假设otc2otf和ttx已经在系统PATH中
    os.chdir(backup_dir)
    run_powershell_command("otc2otf msyh.ttc")
    run_powershell_command("otc2otf msyhl.ttc")
    run_powershell_command("otc2otf msyhbd.ttc")

    # 提取name表
    run_powershell_command("ttx -t name MicrosoftYaHei.ttf")
    run_powershell_command("ttx -t name MicrosoftYaHeiUI.ttf")
    run_powershell_command("ttx -t name MicrosoftYaHeiLight.ttf")
    run_powershell_command("ttx -t name MicrosoftYaHeiUILight.ttf")
    run_powershell_command("ttx -t name MicrosoftYaHei-Bold.ttf")
    run_powershell_command("ttx -t name MicrosoftYaHeiUI-Bold.ttf")

    # 删除临时TTF文件
    for file in os.listdir(backup_dir):
        if file.startswith("MicrosoftYaHei") and file.endswith(".ttf"):
            os.remove(os.path.join(backup_dir, file))

    os.chdir(rootdir)


def download_file(url, filename):
    try:
        urllib.request.urlretrieve(url, filename)
    except Exception as e:
        error(f"下载失败: {filename}. 错误: {str(e)}")


def convert_fonts(rootdir):
    info("正在转换目标字体...")
    target_font_dir = os.path.join(rootdir, "target-fonts")
    backup_dir = os.path.join(rootdir, "msyh-backup")
    os.chdir(target_font_dir)
    required_files = [
        "Regular.ttf",
        "Light.ttf",
        "Bold.ttf",
    ]
    for file in required_files:
        if not os.path.exists(os.path.join(target_font_dir, file)):
            error(f"转换字体失败: {file} 不存在")

    # 删除可能存在的旧文件
    for file in os.listdir(target_font_dir):
        if file.startswith("MicrosoftYaHei") and (
            file.endswith(".ttf") or file.endswith(".otf")
        ):
            os.remove(os.path.join(target_font_dir, file))

    # 使用ttx合并字体和name表
    run_powershell_command(
        f"ttx -b -d \"{target_font_dir}\" -m Regular.ttf \"{os.path.join(backup_dir, 'MicrosoftYaHei.ttx')}\""
    )
    run_powershell_command(
        f"ttx -b -d \"{target_font_dir}\" -m Regular.ttf \"{os.path.join(backup_dir, 'MicrosoftYaHeiUI.ttx')}\""
    )
    run_powershell_command(
        f"ttx -b -d \"{target_font_dir}\" -m Light.ttf \"{os.path.join(backup_dir, 'MicrosoftYaHeiLight.ttx')}\""
    )
    run_powershell_command(
        f"ttx -b -d \"{target_font_dir}\" -m Light.ttf \"{os.path.join(backup_dir, 'MicrosoftYaHeiUILight.ttx')}\""
    )
    run_powershell_command(
        f"ttx -b -d \"{target_font_dir}\" -m Bold.ttf \"{os.path.join(backup_dir, 'MicrosoftYaHei-Bold.ttx')}\""
    )
    run_powershell_command(
        f"ttx -b -d \"{target_font_dir}\" -m Bold.ttf \"{os.path.join(backup_dir, 'MicrosoftYaHeiUI-Bold.ttx')}\""
    )

    # 使用otf2otc合并字体
    run_powershell_command(
        "otf2otc MicrosoftYaHei.ttf MicrosoftYaHeiUI.ttf -o msyh.ttc"
    )
    run_powershell_command(
        "otf2otc MicrosoftYaHeiLight.ttf MicrosoftYaHeiUILight.ttf -o msyhl.ttc"
    )
    run_powershell_command(
        "otf2otc MicrosoftYaHei-Bold.ttf MicrosoftYaHeiUI-Bold.ttf -o msyhbd.ttc"
    )

    # 清理临时文件
    for file in os.listdir(target_font_dir):
        if file.startswith("MicrosoftYaHei") and file.endswith(".ttf"):
            os.remove(os.path.join(target_font_dir, file))
    os.chdir(rootdir)


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

def confirm(rootdir):
    """确认目标字体"""
    info("正在确认目标字体...")
    target_font_dir = os.path.join(rootdir, "target-fonts")
    required_files = ["Regular.ttf", "Light.ttf", "Bold.ttf"]
    for file in required_files:
        if not os.path.exists(os.path.join(target_font_dir, file)):
            error(f"确认字体失败: {file} 不存在")

def replace_files(rootdir):
    """替换系统字体文件"""
    target_font_dir = os.path.join(rootdir, "target-fonts")
    backup_dir = os.path.join(rootdir, "msyh-backup")

    os.chdir(target_font_dir)

    # 检查转换后的字体是否存在
    converted = True
    required_files = ["msyh.ttc", "msyhl.ttc", "msyhbd.ttc"]
    for file in required_files:
        if not os.path.exists(os.path.join(target_font_dir, file)):
            error(f"替换字体失败: {file} 不存在")

    info("正在替换字体文件...")

    # 获取文件所有权
    run_powershell_command(R"takeown /F C:\Windows\Fonts\msyh* /A")
    run_powershell_command(R"icacls C:\Windows\Fonts\msyh* /grant Administrators:F")

    # 删除原字体文件
    run_powershell_command(
        R"Remove-Item -Path 'C:\Windows\Fonts\msyh*' -Force -Recurse"
    )

    # 复制新字体文件
    for file in required_files:
        src = os.path.join(target_font_dir, file)
        dst = os.path.join(R"C:\Windows\Fonts", file)
        shutil.copy2(src, dst)

    # 恢复权限
    run_powershell_command(R"takeown /F C:\Windows\Fonts\msyh* /A")
    run_powershell_command(R"icacls C:\Windows\Fonts\msyh* /grant Administrators:F")
    run_powershell_command(
        R'icacls C:\windows\Fonts\msyh* /C /setowner "NT SERVICE\TrustedInstaller"'
    )
    run_powershell_command(
        f"icacls C:\\windows\\Fonts\\ /C /restore \"{os.path.join(backup_dir, 'acl')}\""
    )

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

    # 检查注册表中是否存在原始字体项
    result = run_powershell_command(
        R"Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'; if ($?) { Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts' -Name 'Microsoft Yahei & Microsoft Yahei UI (TrueType)' }",
        capture_output=True,
    )
    if result:
        has_original_fonts = (
            "Microsoft Yahei & Microsoft Yahei UI (TrueType)" in result.stdout
        )
    else:
        has_original_fonts = False
    try:
        if has_original_fonts:
            # 首次运行：备份、转换、删除注册表(注销后再登录替换)
            backup(rootdir)
            confirm(rootdir)
            convert_fonts(rootdir)
            delete_registry_entries()
        else:
            info("未发现原始微软雅黑字体，跳过备份")
            # 后续运行：直接替换文件
            replace_files(rootdir)

        # 提示用户注销
        warning("点击任意键注销系统")
        input()

        # 注销系统
        run_powershell_command("shutdown -L")

    except Exception as e:
        error(f"发生错误: {str(e)}")


if __name__ == "__main__":
    main()
