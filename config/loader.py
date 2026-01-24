import json
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class MapperConfig:
    source_file: str
    registry_entry: str
    font_name_display: str
    backup_dir: str
    fake_file: Optional[str] = None
    output_file: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MapperConfig':
        return cls(
            source_file=data['source_file'],
            registry_entry=data['registry_entry'],
            font_name_display=data['font_name_display'],
            backup_dir=data['backup_dir'],
            fake_file=data.get('fake_file'),
            output_file=data.get('output_file')
        )

@dataclass
class ConverterConfig:
    type: str
    mappers: List[MapperConfig]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConverterConfig':
        return cls(
            type=data['type'],
            mappers=[MapperConfig.from_dict(m) for m in data['mappers']]
        )

@dataclass
class Config:
    converters: List[ConverterConfig]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        return cls(
            converters=[ConverterConfig.from_dict(c) for c in data['converters']]
        )

def load_config(config_path: str) -> Config:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config对象
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Config.from_dict(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件JSON格式错误: {e}")
    except KeyError as e:
        raise ValueError(f"配置文件缺少必要字段: {e}")
    except Exception as e:
        raise RuntimeError(f"加载配置文件失败: {e}")
