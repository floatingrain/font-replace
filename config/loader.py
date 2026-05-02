import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utils.common import error, warning


@dataclass
class MapperConfig:
    source_file: str
    registry_entry: str
    font_name_display: str
    backup_dir: str
    fake_file: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MapperConfig":
        return cls(
            source_file=data["source_file"],
            registry_entry=data["registry_entry"],
            font_name_display=data["font_name_display"],
            fake_file=data["fake_file"],
            backup_dir="backup",
        )


@dataclass
class ConverterConfig:
    type: str
    mappers: List[MapperConfig]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConverterConfig":
        return cls(
            type=data["type"],
            mappers=[MapperConfig.from_dict(m) for m in data["mappers"]],
        )


@dataclass
class Config:
    converters: List[ConverterConfig]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(
            converters=[ConverterConfig.from_dict(c) for c in data["converters"]]
        )


def load_config(config_path: str) -> Config | None:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        Config对象
    """
    if not os.path.exists(config_path):
        error(f"配置文件不存在: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Config.from_dict(data)
    except json.JSONDecodeError as e:
        error(f"配置文件JSON格式错误: {e}")
    except KeyError as e:
        error(f"配置文件缺少必要字段: {e}")
    except Exception as e:
        error(f"加载配置文件失败: {e}")


def resource_check(config: Config) -> bool:
    """
    检查配置文件中的以下资源是否存在以及合法

    - source_file 是否存在
    - fake_file 是否合法（若提供）
    - registry_entry 是否存在于注册表

    Args:
        config: 配置对象

    Returns:
        前置资源是否全部合法
    """
    from utils.common import run_powershell_command

    valid = True

    for converter in config.converters:
        for mapper in converter.mappers:
            # 检查 source_file 是否存在
            if not os.path.exists(mapper.source_file):
                warning(
                    f"[{mapper.font_name_display}] 源文件不存在: {mapper.source_file}"
                )
                valid = False

            # 检查 fake_file 是否存在（可选字段，但若提供则必须存在）
            if mapper.fake_file is not None and not os.path.exists(mapper.fake_file):
                warning(
                    f"[{mapper.font_name_display}] 替换字体不存在: {mapper.fake_file}"
                )
                valid = False

            # 检查 registry_entry 是否存在于注册表
            cmd = (
                f"Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' "
                f"-Name '{mapper.registry_entry}' -ErrorAction SilentlyContinue"
            )
            result = run_powershell_command(cmd, capture_output=True, check=False)
            if result is None or not result.stdout.strip():
                warning(
                    f"[{mapper.font_name_display}] 注册表项不存在: {mapper.registry_entry}"
                )
                valid = False

    return valid


def restore_resource_check(config: Config) -> bool:
    """
    检查备份目录中的资源是否完整，用于恢复流程

    - backup_dir 是否存在
    - 备份字体文件是否存在且非空
    - .acl 文件是否存在（缺失仅警告）

    Args:
        config: 配置对象

    Returns:
        备份资源是否全部合法
    """
    valid = True

    for converter in config.converters:
        for mapper in converter.mappers:
            # 检查 backup_dir 是否存在
            if not os.path.exists(mapper.backup_dir):
                warning(
                    f"[{mapper.font_name_display}] 备份目录不存在: {mapper.backup_dir}"
                )
                valid = False
                continue

            # 检查备份字体文件是否存在
            backup_font = os.path.join(
                mapper.backup_dir, os.path.basename(mapper.source_file)
            )
            if not os.path.exists(backup_font):
                warning(
                    f"[{mapper.font_name_display}] 备份字体文件不存在: {backup_font}"
                )
                valid = False
                continue

            # 检查备份字体文件是否非空
            if os.path.getsize(backup_font) == 0:
                warning(f"[{mapper.font_name_display}] 备份字体文件为空: {backup_font}")
                valid = False

            # 检查 .acl 文件是否存在（非致命）
            acl_filename = (
                os.path.splitext(os.path.basename(mapper.source_file))[0] + ".acl"
            )
            acl_file = os.path.join(mapper.backup_dir, acl_filename)
            if not os.path.exists(acl_file):
                warning(
                    f"[{mapper.font_name_display}] ACL备份文件不存在（将跳过权限恢复）: {acl_file}"
                )

    return valid
