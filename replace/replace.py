from config.loader import Config
from converters import TTCConverter, TTFConverter
from utils.common import error, warning


def run_replace(config: Config):
    """执行正向字体替换"""
    try:
        for converter_config in config.converters:
            converter_type = converter_config.type.lower()

            if converter_type == "ttc":
                converter = TTCConverter(converter_config)
            elif converter_type == "ttf":
                converter = TTFConverter(converter_config)
            else:
                warning(f"未知的转换器类型: {converter_type}，跳过")
                continue

            converter.run()

    except Exception as e:
        import traceback
        traceback.print_exc()
        error(f"程序执行出错: {e}")
