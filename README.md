# Windows 字体替换工具

本项目是一个模块化的 Python 工具，用于替换 Windows 系统字体（如微软雅黑、Segoe UI 等）。它支持 TTC 和 TTF 字体文件，并可以通过 JSON 配置文件进行灵活配置。

核心原理：提取原字体的 `name` 表（元数据），合并到替换字体中，使 Windows 将替换字体识别为原字体。

## 目录结构

- `main.py`: 程序入口（CLI）
- `config/`: 配置加载逻辑及数据类定义
- `replacer/`: 字体替换核心逻辑（`base.py` 基类、`ttc.py` TTC 转换器、`ttf.py` TTF 转换器、`replace.py` 编排器）
- `restorer/`: 字体还原逻辑（暂未实现）
- `utils/`: 通用工具（`common.py` 系统操作、`font.py` 字体操作）
- `fake-fonts/`: 内置替换字体（MiSans 系列）
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

你需要手动创建配置文件（参考以下示例），并在运行时通过 `-c` 参数指定路径：

- **通用模板**：仓库根目录下的 `config-example.json`

- **微软雅黑 & Segoe UI 替换**：参考仓库根目录下的 `yahei&segoe.json`

**配置说明**：
参考项目根目录中的 `config-example.json`。json 文件根路径必须包含一个 `converters` 数组， `converters` 数组下可包含两种字体替换器，一种为 `ttc`，一种为 `ttf` ，替换器由 `type` 字段指定。然后，每个 `converter` 下可包含多个 mapper 对象组成的 `mappers` 数组，每个 mapper 由以下字段组成：

- `source_file`：Windows 系统原始字体文件的路径
- `fake_file`：用来替换上述原始字体的字体文件路径（TTC 类型中，同一 converter 内只需在第一个 mapper 中指定）
- `registry_entry`：Windows 系统原始字体对应的注册表键名
- `font_name_display`：在程序执行过程中打印 log 时用于提示的字体名称

> 备份目录由程序自动设置为工作目录下的 `backup/`，无需在配置文件中指定。

### 2. 运行程序

需以管理员权限运行，`-c` 参数指定配置文件路径：

**替换字体：**

```powershell
sudo uv run python main.py replace -c my_config.json
```

或者，以管理员权限运行打包后产生的可执行文件：

```powershell
sudo font-replace.exe replace -c my_config.json
```

### 3. 生效

程序执行完毕后，会提示按任意键重启系统以使字体替换生效。

### 4. 注意事项

* **备份**：程序会自动备份原字体及其 ACL 权限到工作目录下的 `backup/`。
* **还原**：`restore` 子命令目前尚未实现。还原功能的代码框架已存在于 `restorer/restore.py` 中，但尚未启用。
* **风险**：修改系统字体有一定风险，请在执行本程序之前为系统创建还原点。

## 开发

* `replacer/base.py`: 定义了转换器的基本流程（备份 → 准备 → 转换 → 安装）。若要添加新的转换器类型，请继承 `BaseConverter` 并实现 `prepare_resource()`、`convert()`、`add_registry_entries()` 三个抽象方法。
* `replacer/replace.py`: 替换编排器，按 converter type 实例化对应转换器并执行。
* `replacer/ttc.py`: TTC 转换器，处理 TrueType Collection 文件（解包 → 提取名称表 → 合并 → 重新打包）。
* `replacer/ttf.py`: TTF 转换器，处理单个 TrueType 文件（提取名称表 → 合并）。
* `restorer/restore.py`: 还原编排器（代码已注释，暂未启用）。
* `utils/common.py`: 系统操作（PowerShell 子进程、管理员检查、进程终止、文件所有权管理、日志输出）。
* `utils/font.py`: 字体操作（TTC 解包/打包、名称表提取/合并），基于 fonttools。

本项目提供了 `main.spec` 文件，可以直接使用 PyInstaller 打包：

```bash
uv run pyinstaller main.spec --clean
```

打包完成后，可执行文件位于 `dist/` 目录下。
