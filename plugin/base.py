#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from utils import (
    run_powershell_command,
    take_ownership,
    restore_ownership,
    delete_font_files,
    copy_font_files,
    warning,
    info,
    error,
)


class FontPlugin:
    """字体处理插件基类"""
    
    font_name = None
    font_name_display = None
    backup_dir_name = None
    fake_font_dir_name = None
    file_pattern = None
    source_files = []
    output_files = []
    registry_entries = []
    name_table_files = []
    required_fake_files = []
    ttc_files = []
    name_table_mapping = {}
    ttc_files_dict = {}
    registry_entries_dict = {}
    
    def backup(self, rootdir):
        """备份原有字体"""
        backup_dir = os.path.join(rootdir, self.backup_dir_name)
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        os.makedirs(backup_dir)
        info(f"正在备份{self.font_name_display}字体...")
        run_powershell_command(
            f"icacls C:\\Windows\\Fonts\\{self.file_pattern} /save '{os.path.join(backup_dir, 'acl')}' /T"
        )
        for file in os.listdir("C:\\Windows\\Fonts"):
            if any(file.startswith(prefix) for prefix in self.source_files):
                src = os.path.join("C:\\Windows\\Fonts", file)
                dst = os.path.join(backup_dir, file)
                shutil.copy2(src, dst)
        os.chdir(backup_dir)
        for ttc in self.ttc_files:
            run_powershell_command(f"otc2otf {ttc}")
        for name_file in self.name_table_files:
            run_powershell_command(f"ttx -t name {name_file}")
        for file in os.listdir(backup_dir):
            if file.endswith(".ttf") and any(file.startswith(prefix) for prefix in self.source_files):
                os.remove(os.path.join(backup_dir, file))
        os.chdir(rootdir)
    
    def convert(self, rootdir):
        """转换目标字体"""
        info("正在转换目标字体...")
        target_font_dir = os.path.join(rootdir, self.fake_font_dir_name)
        backup_dir = os.path.join(rootdir, self.backup_dir_name)
        os.chdir(target_font_dir)
        for file in self.required_fake_files:
            if not os.path.exists(os.path.join(target_font_dir, file)):
                error(f"转换字体失败: {file} 不存在")
        for file in os.listdir(target_font_dir):
            if file.endswith((".ttf", ".otf")) and any(file.startswith(prefix) for prefix in self.source_files):
                os.remove(os.path.join(target_font_dir, file))
        for name_file, source_font in self.name_table_mapping.items():
            run_powershell_command(
                f'ttx -b -d "{target_font_dir}" -m {source_font} "{os.path.join(backup_dir, name_file)}"'
            )
        for ttc_name, font_list in self.ttc_files_dict.items():
            fonts_str = " ".join(font_list)
            run_powershell_command(f"otf2otf {fonts_str} -o {ttc_name}")
        for file in os.listdir(target_font_dir):
            if file.endswith(".ttf") and any(file.startswith(prefix) for prefix in self.source_files):
                os.remove(os.path.join(target_font_dir, file))
        os.chdir(rootdir)
    
    def delete_registry(self):
        """删除注册表项"""
        warning("正在删除注册表项...")
        for entry in self.registry_entries:
            run_powershell_command(
                f"Remove-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' -Name '{entry}' -Force -ErrorAction SilentlyContinue"
            )
    
    def confirm(self, rootdir):
        """确认目标字体"""
        info("正在确认目标字体...")
        target_font_dir = os.path.join(rootdir, self.fake_font_dir_name)
        for file in self.required_fake_files:
            if not os.path.exists(os.path.join(target_font_dir, file)):
                error(f"确认字体失败: {file} 不存在")
    
    def replace(self, rootdir):
        """替换系统字体文件"""
        target_font_dir = os.path.join(rootdir, self.fake_font_dir_name)
        backup_dir = os.path.join(rootdir, self.backup_dir_name)
        os.chdir(target_font_dir)
        for file in self.output_files:
            if not os.path.exists(os.path.join(target_font_dir, file)):
                error(f"替换字体失败: {file} 不存在")
        info("正在替换字体文件...")
        take_ownership(f'C:\\Windows\\Fonts\\{self.file_pattern}')
        delete_font_files(f'C:\\Windows\\Fonts\\{self.file_pattern}')
        copy_font_files(target_font_dir, "C:\\Windows\\Fonts", self.output_files)
        restore_ownership(f'C:\\Windows\\Fonts\\{self.file_pattern}', backup_dir)
        for name, value in self.registry_entries_dict.items():
            run_powershell_command(
                f"New-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' -Name '{name}' -Value '{value}' -PropertyType String -Force"
            )
        os.chdir(rootdir)
    
    def get_registry_check_query(self):
        """获取检查注册表的查询命令"""
        first_entry = self.registry_entries[0] if self.registry_entries else None
        if first_entry:
            return f"Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts'; if ($?) {{ Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' -Name '{first_entry}' }}"
        return None
