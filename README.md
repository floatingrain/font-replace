# Windows 字体替换工具

本项目是一个模块化的 Python 工具，用于替换 Windows 系统字体（如微软雅黑、Segoe UI 等）。它支持 TTC 和 TTF 字体文件，并可以通过 JSON 配置文件进行灵活配置。

## 目录结构

- `main.py`: 程序入口
- `config/`: 配置文件及加载逻辑
  - `config.json`: 默认配置文件（需手动创建）
- `converters/`: 字体转换核心逻辑 (TTC, TTF)
- `utils/`: 通用工具 (PowerShell, FontTools 等)
- `config-example.json`: 配置文件示例模板
- `yahei&segoe.json`: 微软雅黑与 Segoe UI 替换配置参考
- `main.spec`: PyInstaller 打包配置文件

## 依赖

本项目使用 `uv` 管理依赖，需要 Python >= 3.14。

### 安装依赖

```bash
uv sync
```

## 使用方法

### 1. 准备配置文件

程序默认读取 `config/config.json`。你可以复制根目录下的示例文件进行配置：

- **通用模板**：仓库根目录下的 `config-example.json`

- **微软雅黑 & Segoe UI 替换**：参考仓库根目录下的`yahei&segoe.json`

**配置说明**：
参考项目根目录中的 `config-example.json`。json 文件根路径必须包含一个 `converters` 数组， `converters` 数组下可包含两种字体替换器，一种为 `ttc`，一种为 `ttf` ，替换器由 `type` 字段指定。然后，每个 `converter` 下可包含多个 mapper 对象组成的 `mappers` 数组，每个 mapper 由以下五个字段组成：

- source_file：Windows 系统原始字体文件的路径

- fake_file：用来替换上述原始字体的字体文件路径

- registry_entry：Windows 系统原始字体文件的路径的注册表键

- font_name_display：在程序执行过程中打印 log 时用于提示的字体名称

- backup_dir：用于备份 Windows 系统原始字体文件的备份文件夹路径

### 2. 运行程序

需以管理员权限运行：

```powershell
sudo uv run python main.py --config my_config.json
```

或者，以管理员权限运行打包后产生的main.exe：

```powershell
sudo main.exe --config my_config.json
```

### 3. 生效

程序执行完毕后，会提示注销系统。注销并重新登录后，字体替换即生效。另外，有时可能需要重新启动系统。

### 4. 注意事项

* **备份**：程序会自动备份原字体到配置文件指定的 `backup_dir`。
* **风险**：修改系统字体有一定风险，请在执行本程序之前为系统创建还原点。
* **还原**：目前暂无还原逻辑。但可以想到的是，我们能够使用备份的 Windows 原始字体作为 fake_font 反向替换回去。

## 开发

`utils/common.py`: 包含系统操作、权限管理、日志等。

* `converters/base.py`: 定义了转换器的基本流程 (备份 -> 准备 -> 转换 -> 安装)。
* 若要添加新的转换器类型，请继承 `BaseConverter` 并实现相应方法。

本项目提供了 `main.spec` 文件，可以直接使用 PyInstaller 打包：

```bash
uv run pyinstaller main.spec --clean
```

打包完成后，可执行文件位于 `dist/` 目录下。
