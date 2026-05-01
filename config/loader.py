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
    fake_file: Optional[str] = None
    output_file: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MapperConfig":
        return cls(
            source_file=data["source_file"],
            registry_entry=data["registry_entry"],
            font_name_display=data["font_name_display"],
            backup_dir=data["backup_dir"],
            fake_file=data.get("fake_file"),
            output_file=data.get("output_file"),
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
                warning(f"[{mapper.font_name_display}] 源文件不存在: {mapper.source_file}")
                valid = False

            # 检查 fake_file 是否存在（可选字段，但若提供则必须存在）
            if mapper.fake_file is not None and not os.path.exists(mapper.fake_file):
                warning(f"[{mapper.font_name_display}] 替换字体不存在: {mapper.fake_file}")
                valid = False

            # 检查 registry_entry 是否存在于注册表
            cmd = (
                f"Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts' "
                f"-Name '{mapper.registry_entry}' -ErrorAction SilentlyContinue"
            )
            result = run_powershell_command(cmd, capture_output=True, check=False)
            if result is None or not result.stdout.strip():
                warning(f"[{mapper.font_name_display}] 注册表项不存在: {mapper.registry_entry}")
                valid = False

    return valid
