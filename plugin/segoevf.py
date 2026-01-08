#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from plugin.base import FontPlugin


class SegoeVFPlugin(FontPlugin):
    """Segoe UI Variable 字体处理插件"""
    
    font_name = "segoevf"
    font_name_display = "Segoe UI Variable"
    backup_dir_name = "backup/segoevf"
    fake_font_dir_name = "fake-font/segoevf"
    file_pattern = "SegUIVar.ttf"
    source_files = ["SegUIVar"]
    output_files = ["SegUIVar.ttf"]
    registry_entries = ["Segoe UI Variable (TrueType)"]
    name_table_files = ["SegUIVar.ttx"]
    required_fake_files = ["MiSansLatinVF.ttf"]
    ttc_files = []
    name_table_mapping = {
        "SegUIVar.ttf": "MiSansLatinVF.ttf",
    }
    ttc_files_dict = {}
    registry_entries_dict = {
        "Segoe UI Variable (TrueType)": "SegUIVar.ttf",
    }
    
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
            if file == "SegUIVar.ttf":
                src = os.path.join("C:\\Windows\\Fonts", file)
                dst = os.path.join(backup_dir, file)
                shutil.copy2(src, dst)
        os.chdir(backup_dir)
        run_powershell_command("ttx -t name SegUIVar.ttf")
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
        run_powershell_command(
            f'ttx -b -d "{target_font_dir}" -m MiSansLatinVF.ttf "{os.path.join(backup_dir, "SegUIVar.ttx")}"'
        )
        os.chdir(rootdir)
    
    def replace(self, rootdir):
        """替换系统字体文件"""
        target_font_dir = os.path.join(rootdir, self.fake_font_dir_name)
        backup_dir = os.path.join(rootdir, self.backup_dir_name)
        os.chdir(target_font_dir)
        if not os.path.exists(os.path.join(target_font_dir, "SegUIVar.ttf")):
            error("替换字体失败: SegUIVar.ttf 不存在")
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
