import os
import subprocess
import sys
from typing import List, Optional, Set

import psutil


def info(message: str) -> None:
    """显示蓝色提示信息"""
    print(f"\033[94m{message}\033[0m")


def warning(message: str) -> None:
    """显示黄色警告信息"""
    print(f"\033[93m{message}\033[0m", file=sys.stderr)


def error(message: str) -> None:
    """显示红色错误信息并退出"""
    print(f"\033[91m{message}\033[0m", file=sys.stderr)
    input("按任意键退出...")
    sys.exit(1)


def run_powershell_command(
    command: str, capture_output: bool = True, check: bool = True
) -> Optional[subprocess.CompletedProcess]:
    """
    运行PowerShell命令并进行错误监测

    Args:
        command: PowerShell命令字符串
        capture_output: 是否捕获输出
        check: 是否检查返回值（非0抛出异常）

    Returns:
        subprocess.CompletedProcess 或 None (当出错且未抛出异常时)
    """
    cmd = ["powershell.exe", "-Command", command]
    try:
        # 仅在非捕获模式下打印命令，避免日志过于杂乱，或者使用debug级别日志(此处简化为info)
        # info(f"执行命令: {command}")
        result = subprocess.run(
            cmd, capture_output=capture_output, check=check, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        warning(f"命令执行错误：{e.stderr if e.stderr else e}")
        if check:
            raise
        return None


def is_admin() -> bool:
    """检查是否以管理员权限运行"""
    try:
        cmd = "([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)"
        result = run_powershell_command(cmd, capture_output=True, check=False)
        if result and result.stdout:
            return result.stdout.strip().lower() == "true"
        return False
    except Exception as e:
        warning(f"检查管理员权限时出错: {e}")
        return False


def kill_processes_using_files(files: List[str]) -> None:
    """
    查找并强行终止占用指定文件（一个或多个）的进程

    """
    file_paths = {f.lower() for f in files}
    display_msg = f"{len(files)} 个文件"

    info(f"正在扫描占用 {display_msg} 的进程...")
    target_pids: Set[int] = set()

    try:
        for proc in psutil.process_iter(["pid", "name", "open_files"]):
            try:
                open_files = proc.info["open_files"] or []
                for file in open_files:
                    if file.path.lower() in file_paths:
                        pid = proc.info["pid"]
                        warning(
                            f"发现占用 {file.path} 的进程: {proc.info['name']} (PID {pid})"
                        )
                        target_pids.add(pid)
            except psutil.NoSuchProcess, psutil.AccessDenied:
                continue
    except Exception as e:
        warning(f"扫描进程时出错: {e}")

    if target_pids:
        for pid in target_pids:
            try:
                proc = psutil.Process(pid)
                proc.kill()
                info(f"已终止进程 {proc.name()} (PID {pid})")
            except psutil.NoSuchProcess, psutil.AccessDenied:
                warning(f"无法终止进程 PID {pid}")
    else:
        # info("未找到明显占用字体文件的进程")
        pass


def take_ownership(file_path: str) -> None:
    """获取文件所有权"""
    if not os.path.exists(file_path):
        return
    run_powershell_command(f"takeown /F '{file_path}' /A", check=False)
    run_powershell_command(f"icacls '{file_path}' /grant Administrators:F", check=False)


def restore_ownership(file_path: str, acl_file: str) -> None:
    """恢复文件所有权和权限

    Args:
        file_path: 要恢复权限的文件路径（必须已存在）
        acl_file: 由 icacls /save 生成的ACL备份文件路径
    """
    if not os.path.exists(file_path):
        return

    # 恢复ACL（必须在设置owner之前，因为icacls /restore要求调用者有写DACL权限）
    if os.path.exists(acl_file):
        # icacls /restore 要求 file_path 是acl文件中记录的原路径，
        # 且文件必须已存在于该路径。/C 让它遇到错误继续执行。
        result = run_powershell_command(
            f"icacls '{file_path}' /C /restore '{acl_file}'", check=False
        )
        if result and result.returncode != 0:
            warning(f"ACL恢复可能未完全成功: {file_path}")
    else:
        warning(f"ACL备份文件不存在，跳过恢复: {acl_file}")

    # 最终将所有权交还给 TrustedInstaller
    run_powershell_command(
        f"icacls '{file_path}' /setowner \"NT SERVICE\\TrustedInstaller\"", check=False
    )
