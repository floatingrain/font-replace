import os
import shutil
from concurrent.futures import ThreadPoolExecutor

from config.loader import Config, MapperConfig
from utils.common import (
    error,
    info,
    kill_processes_using_files,
    restore_ownership,
    run_powershell_command,
    take_ownership,
    warning,
)


class RestoreRunner:
    """字体恢复器，从备份目录恢复原始字体"""

    def __init__(self, mapper: MapperConfig):
        self.mapper = mapper

    def validate_backup(self):
        """验证单个 mapper 的备份完整性"""
        backup_font = os.path.join(
            self.mapper.backup_dir, os.path.basename(self.mapper.source_file)
        )
        if not os.path.exists(backup_font):
            error(f"[{self.mapper.font_name_display}] 备份字体文件不存在: {backup_font}")
        if os.path.getsize(backup_font) == 0:
            error(f"[{self.mapper.font_name_display}] 备份字体文件为空: {backup_font}")

    def restore_file(self):
        """恢复字体文件和 ACL 权限"""
        mapper = self.mapper
        backup_font = os.path.join(mapper.backup_dir, os.path.basename(mapper.source_file))
        acl_filename = os.path.splitext(os.path.basename(mapper.source_file))[0] + ".acl"
        acl_file = os.path.join(mapper.backup_dir, acl_filename)

        info(f"正在恢复字体文件: {mapper.source_file}")

        # 获取当前文件所有权
        take_ownership(mapper.source_file)

        # 删除当前文件
        try:
            if os.path.exists(mapper.source_file):
                os.remove(mapper.source_file)
        except OSError as e:
            try:
                temp_backup = mapper.source_file + ".old"
                if os.path.exists(temp_backup):
                    os.remove(temp_backup)
                os.rename(mapper.source_file, temp_backup)
                warning(f"无法直接删除，已重命名为 {temp_backup}")
            except OSError:
                error(f"无法删除或重命名原文件: {mapper.source_file}, {e}")

        # 复制备份文件到系统路径
        try:
            shutil.copy2(backup_font, mapper.source_file)
        except OSError as e:
            error(f"复制备份文件失败: {e}")

        # 恢复 ACL 和所有权
        restore_ownership(mapper.source_file, acl_file)

    def restore_registry(self):
        """恢复注册表项"""
        mapper = self.mapper
        font_filename = os.path.basename(mapper.source_file)

        info(f"正在恢复注册表项: {mapper.registry_entry}")

        # 删除当前注册表项
        cmd = (
            f"Remove-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' "
            f"-Name '{mapper.registry_entry}' -Force -ErrorAction SilentlyContinue"
        )
        run_powershell_command(cmd, check=False)

        # 添加原始注册表项
        cmd = (
            f"New-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' "
            f"-Name '{mapper.registry_entry}' -Value '{font_filename}' -PropertyType String -Force"
        )
        run_powershell_command(cmd, check=False)


def run_restore(config: Config):
    """
    执行字体恢复流程

    Args:
        config: 配置对象
    """
    # 1. 收集所有 mappers 并验证备份
    runners = []
    for converter_config in config.converters:
        for mapper in converter_config.mappers:
            runner = RestoreRunner(mapper)
            runner.validate_backup()
            runners.append(runner)

    if not runners:
        warning("没有需要恢复的字体")
        return

    # 2. 统一终止占用进程
    system_files = [runner.mapper.source_file for runner in runners]
    kill_processes_using_files(system_files)

    # 3. 多线程并行恢复文件
    info(f"正在启动 {len(runners)} 个线程进行字体恢复...")
    with ThreadPoolExecutor(max_workers=len(runners)) as executor:
        list(executor.map(lambda r: r.restore_file(), runners))

    # 4. 统一恢复注册表项
    for runner in runners:
        runner.restore_registry()

    info("所有字体已恢复！")
