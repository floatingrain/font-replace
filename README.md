# Windows 字体替换工具

本项目是一个模块化的 Python 工具，用于替换 Windows 系统字体（如微软雅黑）。它支持 TTC 和 TTF 字体文件，并可以通过 JSON 配置文件进行灵活配置。

## 目录结构

- `main.py`: 程序入口
- `config/`: 配置文件及加载逻辑
- `converters/`: 字体转换核心逻辑 (TTC, TTF)
- `utils/`: 通用工具 (PowerShell, FontTools)

## 依赖

需要安装 Python 3 以及以下依赖：
- `psutil`
- `afdko` (提供 otc2otf, otf2otc)
- `fonttools` (提供 ttx)

```bash
pip install -r Pipfile
# 或者
pip install psutil afdko fonttools
```

## 使用方法

1. **准备配置文件**
   
   复制 `config/config-example.json` 为 `config/config.json`，并根据需要修改。

   ```json
   {
     "converters": [
       {
         "type": "ttc",
         "mappers": [
           {
             "source_file": "C:\\Windows\\Fonts\\msyh.ttc",
             "fake_file": "path\\to\\your\\replacement.ttf",
             "registry_entry": "Microsoft YaHei & Microsoft YaHei UI (TrueType)",
             "font_name_display": "Microsoft YaHei",
             "backup_dir": ".\\backup\\msyh"
           }
         ]
       }
     ]
   }
   ```

2. **运行程序**

   需以管理员权限运行（程序会自动请求）：

   ```bash
   python main.py
   # 或者指定配置文件
   python main.py --config my_config.json
   ```

3. **生效**

   程序执行完毕后，会提示注销系统。注销并重新登录后，字体替换即生效。

## 注意事项

- **备份**: 程序会自动备份原字体到配置文件指定的 `backup_dir`。
- **风险**: 修改系统字体有一定风险，可能导致某些程序显示异常或系统不稳定，请谨慎操作。
- **还原**: 目前需手动从 `backup_dir` 还原（后续版本可支持自动还原）。

## 开发说明

- `utils/common.py`: 包含系统操作、权限管理、日志等。
- `converters/base.py`: 定义了转换器的基本流程 (备份 -> 准备 -> 转换 -> 安装)。
- 若要添加新的转换器类型，请继承 `BaseConverter` 并实现相应方法。
