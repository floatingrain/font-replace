import os
import shutil
from abc import ABC, abstractmethod
from typing import List
from config.loader import ConverterConfig, MapperConfig
from utils import info, warning, error, run_powershell_command, take_ownership, restore_ownership, kill_processes_using_files

class BaseConverter(ABC):
    """转换器基类"""

    def __init__(self, config: ConverterConfig):
        self.config = config
        self.mappers = config.mappers

    def run(self):
        """执行转换流程"""
        info(f"开始处理转换器: {self.config.type}")
        self.backup_and_prepare()
        self.convert()
        self.install()
        info(f"转换器 {self.config.type} 处理完成")

    def backup_and_prepare(self):
        """备份原字体并准备资源"""
        for mapper in self.mappers:
            info(f"正在备份 {mapper.font_name_display}...")
            if not os.path.exists(mapper.source_file):
                error(f"源文件不存在: {mapper.source_file}")

            # 创建备份目录
            if not os.path.exists(mapper.backup_dir):
                os.makedirs(mapper.backup_dir)

            # 备份ACL
            acl_file = os.path.join(mapper.backup_dir, "acl")
            # 注意：icacls save 需要文件路径
            run_powershell_command(f"icacls '{mapper.source_file}' /save '{acl_file}' /T", check=False)

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

        # 2. 替换文件
        for mapper in self.mappers:
            self.replace_file(mapper)

        # 3. 添加新注册表项 (由子类实现)
        self.add_registry_entries()

    def replace_file(self, mapper: MapperConfig):
        """替换单个字体文件"""
        if not mapper.output_file:
            # 如果没有指定输出文件，可能是在 convert 阶段生成的中间文件，或者配置错误
            # 这里假设 convert 阶段生成了 mapper.output_file 指向的文件
            warning(f"未指定输出文件，跳过替换: {mapper.font_name_display}")
            return

        target_file = mapper.output_file
        system_file = mapper.source_file

        if not os.path.exists(target_file):
            error(f"目标字体文件不存在: {target_file}")

        info(f"正在替换: {system_file}")
        
        # 获取所有权
        take_ownership(system_file)
        
        # 尝试终止占用进程
        kill_processes_using_files(system_file)

        # 删除原文件
        try:
            if os.path.exists(system_file):
                os.remove(system_file)
        except OSError as e:
            # 如果删除失败，尝试移动到临时目录（Windows下有时允许重命名正在使用的文件）
            try:
                temp_backup = system_file + ".old"
                if os.path.exists(temp_backup):
                    os.remove(temp_backup)
                os.rename(system_file, temp_backup)
                warning(f"无法直接删除，已重命名为 {temp_backup}")
            except OSError:
                error(f"无法删除或重命名原文件: {system_file}, {e}")

        # 复制新文件
        try:
            shutil.copy2(target_file, system_file)
        except OSError as e:
            error(f"复制新文件失败: {e}")

        # 恢复权限 (简单恢复为Administrators，具体恢复逻辑可由 restore_ownership 完善)
        # 这里参考参考步骤.py: takeown -> icacls grant Admin -> icacls setowner TrustedInstaller -> restore acl
        # 我们在 utils/common.py 实现了 restore_ownership，调用它
        restore_ownership(system_file, mapper.backup_dir)

    def remove_registry_entries(self):
        """删除注册表项"""
        warning("正在删除注册表项...")
        for mapper in self.mappers:
            cmd = f"Remove-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' -Name '{mapper.registry_entry}' -Force -ErrorAction SilentlyContinue"
            run_powershell_command(cmd, check=False)

    @abstractmethod
    def add_registry_entries(self):
        """添加注册表项，由子类实现"""
        pass
