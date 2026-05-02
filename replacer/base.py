import logging
import os
import shutil
import sys
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from config.loader import ConverterConfig, MapperConfig
from utils.common import (
    kill_processes_using_files,
    restore_ownership,
    run_powershell_command,
    take_ownership,
)


class BaseConverter(ABC):
    """转换器基类"""

    def __init__(self, config: ConverterConfig):
        self.config = config
        self.mappers = config.mappers

    def run(self):
        """执行转换流程"""
        logging.info(f"开始处理转换器: {self.config.type}")
        self._validate_source_files()
        self.backup_and_prepare()
        self.convert()
        self.install()
        logging.info(f"转换器 {self.config.type} 处理完成")

    def _validate_source_files(self):
        """前置校验所有源文件是否存在，任一缺失则终止"""
        missing = []
        for mapper in self.mappers:
            if not os.path.exists(mapper.source_file):
                missing.append(mapper.source_file)
        if missing:
            for path in missing:
                logging.error(f"源文件不存在: {path}")
                input("按任意键退出...")
                sys.exit(1)

    def backup_and_prepare(self):
        """备份原字体并准备资源"""
        for mapper in self.mappers:
            logging.info(f"正在备份 {mapper.font_name_display}...")

            # 创建备份目录
            if not os.path.exists(mapper.backup_dir):
                os.makedirs(mapper.backup_dir)

            # 备份ACL（使用字体名作为文件名，防止多个mapper共享backup_dir时互相覆盖）
            acl_filename = (
                os.path.splitext(os.path.basename(mapper.source_file))[0] + ".acl"
            )
            acl_file = os.path.join(mapper.backup_dir, acl_filename)
            run_powershell_command(
                f"icacls '{mapper.source_file}' /save '{acl_file}' /T", check=False
            )

            # 复制字体文件
            src = mapper.source_file
            dst = os.path.join(mapper.backup_dir, os.path.basename(src))
            shutil.copy2(src, dst)

            # 执行特定于类型的准备工作（如提取名称表）
            self.prepare_resource(mapper)

    @abstractmethod
    def prepare_resource(self, mapper: MapperConfig):
        """准备资源（如提取name表），由子类实现"""
        pass

    @abstractmethod
    def convert(self):
        """执行字体转换/合并，由子类实现"""
        pass

    def install(self):
        """安装新字体"""
        # 1. 删除旧注册表项 (由子类提供具体的注册表项名称)
        self.remove_registry_entries()

        # 2. 统一扫描并结束占用进程
        system_files = [
            mapper.source_file for mapper in self.mappers if mapper.source_file
        ]
        stop_event = kill_processes_using_files(system_files)
        # 3. 替换文件 (多线程并行，带重试)
        max_retries = 10
        if self.mappers:
            logging.info(f"正在启动 {len(self.mappers)} 个线程进行字体替换...")

            def replace_with_retry(mapper):
                for attempt in range(1, max_retries + 1):
                    try:
                        self.replace_file(mapper)
                        return
                    except Exception as e:
                        if attempt < max_retries:
                            logging.warning(
                                f"{mapper.font_name_display} 替换失败 (第 {attempt}/{max_retries} 次): {e}，正在重试..."
                            )
                        else:
                            raise

            with ThreadPoolExecutor(max_workers=len(self.mappers)) as executor:
                futures = [
                    executor.submit(replace_with_retry, mapper)
                    for mapper in self.mappers
                ]
                for future in futures:
                    future.result()

        stop_event.set()

        # 4. 添加新注册表项 (由子类实现)
        self.add_registry_entries()

    def replace_file(self, mapper: MapperConfig):
        """替换单个字体文件"""
        system_file = mapper.source_file
        target_file = os.path.join(
            os.getcwd(), "target-fonts", os.path.basename(mapper.source_file)
        )

        logging.info(f"正在替换: {system_file}")

        # 构造ACL备份文件路径（与 backup_and_prepare 中的命名规则一致）
        acl_filename = os.path.splitext(os.path.basename(system_file))[0] + ".acl"
        acl_file = os.path.join(mapper.backup_dir, acl_filename)

        # 获取所有权
        take_ownership(system_file)

        # 删除原文件
        try:
            if os.path.exists(system_file):
                os.remove(system_file)
        except OSError as e:
            raise RuntimeError(f"无法删除原文件: {e}") from e

        # 复制新文件
        try:
            shutil.copy2(target_file, system_file)
        except OSError as e:
            raise RuntimeError(f"复制新文件失败: {e}") from e

        # 恢复权限和所有权
        restore_ownership(system_file, acl_file)

    def remove_registry_entries(self):
        """删除注册表项"""
        logging.warning("正在删除注册表项...")
        for mapper in self.mappers:
            cmd = f"Remove-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' -Name '{mapper.registry_entry}' -Force -ErrorAction SilentlyContinue"
            run_powershell_command(cmd, check=False)

    @abstractmethod
    def add_registry_entries(self):
        """添加注册表项，由子类实现"""
        pass
