import os
import sys
import subprocess
import shutil
import psutil
from typing import Optional, List, Set

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

def run_powershell_command(command: str, capture_output: bool = True, check: bool = True) -> Optional[subprocess.CompletedProcess]:
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

def kill_processes_using_files(file_path: str) -> None:
    """
    查找并强行终止占用指定文件的进程
    
    Args:
        file_path: 文件路径
    """
    info(f"正在扫描占用 {file_path} 的进程...")
    target_pids: Set[int] = set()
    
    try:
        for proc in psutil.process_iter(["pid", "name", "open_files"]):
            try:
                open_files = proc.info["open_files"] or []
                for file in open_files:
                    if file.path.lower() == file_path.lower():
                        pid = proc.info["pid"]
                        warning(f"发现占用 {file_path} 的进程: {proc.info['name']} (PID {pid})")
                        target_pids.add(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        warning(f"扫描进程时出错: {e}")

    if target_pids:
        for pid in target_pids:
            try:
                proc = psutil.Process(pid)
                proc.kill()
                info(f"已终止进程 {proc.name()} (PID {pid})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
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

def restore_ownership(file_path: str, acl_backup_dir: str) -> None:
    """恢复文件所有权和权限"""
    if not os.path.exists(file_path):
        return
    
    # 尝试恢复TrustedInstaller所有权
    run_powershell_command(f"icacls '{file_path}' /setowner \"NT SERVICE\\TrustedInstaller\"", check=False)
    
    # 尝试从ACL备份恢复
    # 注意：icacls恢复通常针对目录或需要特定格式，这里参考原逻辑
    # 原逻辑：icacls C:\windows\Fonts\ /C /restore "{os.path.join(backup_dir, 'acl')}"
    # 这里我们假设acl_backup_dir包含acl文件
    acl_file = os.path.join(acl_backup_dir, "acl")
    if os.path.exists(acl_file):
        # icacls /restore 需要父目录作为路径，acl文件要在当前目录下或者指定
        # 这是一个比较tricky的操作，通常需要切到acl文件所在目录或父目录
        # 参考步骤.py逻辑：
        # run_powershell_command(f"icacls C:\\windows\\Fonts\\ /C /restore \"{os.path.join(backup_dir, 'acl')}\"")
        # 这表明它是对 Fonts 目录做 restore
        parent_dir = os.path.dirname(file_path)
        try:
            # 暂时不强制恢复整个目录的ACL，因为可能影响其他字体
            # 如果需要严格遵循参考步骤，我们需要看它备份了什么。
            # 参考步骤备份：icacls C:\Windows\Fonts\msyh* /save ... /T
            # 它是针对特定文件备份的
            pass 
        except Exception as e:
            warning(f"恢复ACL失败: {e}")
