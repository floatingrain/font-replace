import logging
import os
import shutil

from config.loader import MapperConfig
from utils.common import run_powershell_command
from utils.font import ttx_extract_name, ttx_merge

from .base import BaseConverter


class TTFConverter(BaseConverter):
    """处理TTF文件的转换器"""

    def prepare_resource(self, mapper: MapperConfig):
        """提取 name 表"""
        backup_file = os.path.join(
            mapper.backup_dir, os.path.basename(mapper.source_file)
        )

        logging.info(f"正在提取名称表: {os.path.basename(backup_file)}")
        ttx_extract_name(backup_file, mapper.backup_dir)

    def convert(self):
        """使用 fake_file 和 提取的 name 表生成新 TTF"""
        for mapper in self.mappers:
            if not mapper.fake_file or not os.path.exists(mapper.fake_file):
                logging.warning(f"未指定 fake_file 或文件不存在: {mapper.fake_file}，跳过转换")
                continue

            # 查找 ttx 文件
            source_basename = os.path.basename(mapper.source_file)
            # 使用 splitext 确保正确替换扩展名，不区分大小写
            ttx_filename = os.path.splitext(source_basename)[0] + ".ttx"

            ttx_file = os.path.join(mapper.backup_dir, ttx_filename)
            if not os.path.exists(ttx_file):
                # 尝试不区分大小写查找
                import glob

                candidates = glob.glob(os.path.join(mapper.backup_dir, "*.ttx"))
                if len(candidates) == 1:
                    ttx_file = candidates[0]
                else:
                    logging.warning(
                        f"未找到对应的名称表文件 {ttx_filename}，跳过: {mapper.font_name_display}"
                    )
                    continue

            # 创建临时构建目录
            build_dir = os.path.join(mapper.backup_dir, "build")
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)

            # 目标文件名
            target_basename = os.path.basename(mapper.source_file)
            output_ttf = os.path.join(build_dir, target_basename)

            logging.info(f"正在生成: {target_basename}")
            # 复制 fake_file
            shutil.copy2(mapper.fake_file, output_ttf)

            # 合并 name 表
            ttx_merge(output_ttf, ttx_file, build_dir)

            # 设置最终输出路径
            if not mapper.output_file:
                target_dir = os.path.join(os.getcwd(), "target-fonts")
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                mapper.output_file = os.path.join(target_dir, target_basename)

            # 复制到输出路径
            os.makedirs(os.path.dirname(mapper.output_file), exist_ok=True)
            if output_ttf != mapper.output_file:
                shutil.copy2(output_ttf, mapper.output_file)

    def add_registry_entries(self):
        """添加注册表项"""
        logging.info("正在更新注册表...")
        for mapper in self.mappers:
            if not mapper.registry_entry:
                continue

            font_filename = os.path.basename(mapper.source_file)

            cmd = f"New-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' -Name '{mapper.registry_entry}' -Value '{font_filename}' -PropertyType String -Force"
            run_powershell_command(cmd, check=False)
