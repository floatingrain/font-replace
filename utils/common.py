import logging
import os
import subprocess
import threading
from typing import List, Optional, Set

import psutil


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
        result = subprocess.run(
            cmd, capture_output=capture_output, check=check, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logging.warning(f"命令执行错误：{e.stderr if e.stderr else e}")
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
        logging.warning(f"检查管理员权限时出错: {e}")
        return False


def kill_processes_using_files(files: List[str]) -> threading.Event:
    """
    查找并强行终止占用指定文件（一个或多个）的进程。
    为每个发现的进程名创建终结者线程，循环执行杀死命令。
    返回停止事件，调用者 set() 后所有线程退出。

    Returns:
        threading.Event — set() 即停止所有终结者线程
    """
    file_paths = {f.lower() for f in files}
    display_msg = f"{len(files)} 个文件"

    logging.info(f"正在扫描占用 {display_msg} 的进程...")
    target_names: Set[str] = set()

    try:
        for proc in psutil.process_iter(["name", "open_files"]):
            try:
                open_files = proc.info["open_files"] or []
                for file in open_files:
                    if file.path.lower() in file_paths:
                        name = proc.info["name"]
                        logging.warning(f"发现占用 {file.path} 的进程: {name}")
                        target_names.add(name)
            except psutil.NoSuchProcess, psutil.AccessDenied:
                continue
    except Exception as e:
        logging.warning(f"扫描进程时出错: {e}")

    stop_event = threading.Event()

    if not target_names:
        stop_event.set()
        return stop_event

    def _terminator(proc_name: str) -> None:
        logging.info(f"终结者线程启动: {proc_name}")
        while not stop_event.is_set():
            run_powershell_command(f"taskkill /IM {proc_name} /F", check=False)
        logging.info(f"终结者线程退出: {proc_name}")

    for name in target_names:
        t = threading.Thread(target=_terminator, args=(name,), daemon=True)
        t.start()

    return stop_event


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
        result = run_powershell_command(
            f"icacls '{file_path}' /C /restore '{acl_file}'", check=False
        )
        if result and result.returncode != 0:
            logging.warning(f"ACL恢复可能未完全成功: {file_path}")
    else:
        logging.warning(f"ACL备份文件不存在，跳过恢复: {acl_file}")

    # 最终将所有权交还给 TrustedInstaller
    run_powershell_command(
        f"icacls '{file_path}' /setowner \"NT SERVICE\\TrustedInstaller\"", check=False
    )
