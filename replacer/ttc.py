import glob
import logging
import os
import shutil

from config.loader import MapperConfig
from utils.common import run_powershell_command
from utils.font import otc2otf, otf2otc, ttx_extract_name, ttx_merge

from .base import BaseConverter


class TTCConverter(BaseConverter):
    """处理TTC文件的转换器"""

    def prepare_resource(self, mapper: MapperConfig):
        """
        1. otc2otf 解包 TTC
        2. ttx 提取 name 表
        """
        backup_file = os.path.join(
            mapper.backup_dir, os.path.basename(mapper.source_file)
        )

        # 1. 解包
        logging.info(f"正在解包 {backup_file} ...")
        otc2otf(backup_file, mapper.backup_dir)

        # 2. 提取 name 表
        # 扫描备份目录下的所有ttf文件 (由otc2otf生成)
        extracted_fonts = glob.glob(os.path.join(mapper.backup_dir, "*.ttf"))
        if not extracted_fonts:
            logging.warning(f"未从 {backup_file} 提取到任何TTF文件")
            return

        for font_file in extracted_fonts:
            logging.info(f"正在提取名称表: {os.path.basename(font_file)}")
            ttx_extract_name(font_file, mapper.backup_dir)

    def convert(self):
        """
        1. 使用 fake_file 和 提取的 name 表生成新 TTF
        2. 合并新 TTF 为 TTC
        """
        for mapper in self.mappers:
            if not mapper.fake_file or not os.path.exists(mapper.fake_file):
                logging.warning(f"未指定 fake_file 或文件不存在: {mapper.fake_file}，跳过转换")
                continue

            # 获取备份目录下的所有 ttx 文件 (name表)
            # 注意：我们需要按照otc2otf生成的ttf文件名来找对应的ttx
            # 实际上，我们需要知道生成TTC的顺序吗？otf2otc 接受多个ttf。
            # 顺序可能重要，但通常 otc2otf 不保证顺序，或者我们需要根据文件名排序？
            # 参考步骤.py 中是硬编码的顺序：MicrosoftYaHei.ttf MicrosoftYaHeiUI.ttf
            # 这里为了通用性，我们按文件名排序，或者不做严格要求（TTC索引可能变化，但Windows通常按PS Name识别）

            ttx_files = sorted(glob.glob(os.path.join(mapper.backup_dir, "*.ttx")))
            if not ttx_files:
                logging.warning(f"未找到名称表文件，跳过: {mapper.font_name_display}")
                continue

            generated_ttfs = []

            # 创建临时构建目录 (在backup下或者单独temp)
            build_dir = os.path.join(mapper.backup_dir, "build")
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)

            for ttx_file in ttx_files:
                # 对应的目标文件名 (例如 MicrosoftYaHei.ttf)
                # ttx文件名通常是 MicrosoftYaHei.ttx
                base_name = os.path.basename(ttx_file).replace(".ttx", ".ttf")
                output_ttf = os.path.join(build_dir, base_name)

                # 先复制 fake_file 到 output_ttf，然后 merge
                # 或者直接 merge -o? ttx -m base_font output_path?
                # utils.ttx_merge 实现是: ttx -b -d output_dir -m base_font ttx_file
                # 这会生成 base_font 的文件名在 output_dir。
                # 这里的 base_font 是 fake_file (例如 source.ttf)。
                # 如果 fake_file 叫 source.ttf，输出会是 source.ttf。
                # 我们需要重命名为 MicrosoftYaHei.ttf。

                logging.info(f"正在生成: {base_name}")
                # 复制 fake_file 到 build_dir 并重命名为目标文件名
                shutil.copy2(mapper.fake_file, output_ttf)

                # 合并 name 表
                ttx_merge(output_ttf, ttx_file, build_dir)

                generated_ttfs.append(output_ttf)

            # 合并为 TTC
            if not mapper.output_file:
                # 如果未配置output_file，默认生成到 current_dir/target-fonts/
                # 或者直接用 source_file 的 basename
                target_dir = os.path.join(os.getcwd(), "target-fonts")
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                mapper.output_file = os.path.join(
                    target_dir, os.path.basename(mapper.source_file)
                )

            # 确保输出目录存在
            os.makedirs(os.path.dirname(mapper.output_file), exist_ok=True)

            logging.info(f"正在合并生成 TTC: {mapper.output_file}")
            otf2otc(generated_ttfs, mapper.output_file)

    def add_registry_entries(self):
        """添加注册表项"""
        logging.info("正在更新注册表...")
        for mapper in self.mappers:
            if not mapper.registry_entry:
                continue

            # 值通常是文件名，例如 msyh.ttc
            # 如果 output_file 是完整路径，我们需要提取文件名，因为 Windows Fonts 注册表通常只存文件名 (如果在Fonts目录下)
            # 或者完整路径 (如果在外部)
            # 替换逻辑是将文件复制到 C:\Windows\Fonts，所以只需文件名
            font_filename = os.path.basename(mapper.source_file)

            cmd = f"New-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' -Name '{mapper.registry_entry}' -Value '{font_filename}' -PropertyType String -Force"
            run_powershell_command(cmd, check=False)
