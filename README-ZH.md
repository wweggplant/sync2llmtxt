# 简介

`sync2txt` 是一个用于将指定目录下的源代码文件自动聚合到指定目录下的单一文本文件的脚本，方便将项目代码整体作为上下文输入给大语言模型（如 LLM/LLMtxt）。该脚本支持自动监控目录变更，实时更新聚合文档，也可手动运行一次性生成。

[English](README.md) 中文

---


# 场景

可以把目标文件指定为Google Drive下的目录，这样就可以把项目代码聚合到Google Drive下，方便在Gemini中使用。

## 主要功能

- **多文件类型支持**：可聚合 `.py`, `.ts`, `.tsx`, `.js`, `.json`, `.md` 等多种常见代码和文本文件
- **智能忽略**：
  - 自动应用 `.gitignore` 规则
  - 支持自定义 `IGNORE_PATTERNS`
  - 自动排除二进制文件、图片等无关内容
- **目录结构导出**：生成美观的树状目录结构（含忽略标记）
- **灵活配置**：
  - 支持 YAML 配置文件
  - 命令行参数覆盖配置
- **高级过滤**：
  - 按文件大小过滤（`--max-size`）
  - 按修改时间过滤（`--since-days`）
- **详细日志**：多级别日志记录，便于调试

## 使用方法

### 安装依赖

```bash
# 主程序依赖
pip install -r requirements.txt
# 测试依赖（可选）
pip install -r requirements-test.txt
```

### 配置方式

#### 1. 配置文件（YAML）

```yaml
MONITORED_CODE_DIR: /path/to/code
OUTPUT_DOCUMENT_PATH: /path/to/output.txt
CODE_FILE_PATTERNS: 
  - '*.py'
  - '*.md'
IGNORE_PATTERNS:
  - node_modules
ENABLE_AUTOMATIC_MONITORING: true
DEBOUNCE_TIME: 2.0
```

#### 2. 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-s/--src` | 源代码目录 | `-s ./src` |
| `-o/--out` | 输出文件路径 | `-o output.txt` |
| `-c/--config` | 配置文件路径 | `-c config.yaml` |
| `--max-size` | 最大文件大小(MB) | `--max-size 2` |
| `--since-days` | 最近修改天数 | `--since-days 7` |

### 运行示例

```bash
# 基本用法
python3 sync2txt.py -s ./project -o output.txt

# 使用配置文件+过滤大文件
python3 sync2txt.py -c config.yaml --max-size 1.5

# 仅同步最近修改的文件
python3 sync2txt.py -s ./src -o out.txt --since-days 3
```

## 测试（待完成）

```bash
# 运行测试
pytest --cov=.

# 生成测试覆盖率报告
pytest --cov=. --cov-report=html
```

## 输出格式示例

```
--- Project Code Context (Manual Run @ 2023-11-15 10:00:00) ---

Included Files (2):
- main.py
- utils/helper.py

--- File: main.py ---

import utils

if __name__ == "__main__":
    print("Hello")

--- File: utils/helper.py ---

def help():
    return "Help message"

--- Directory Structure ---
project/
├── main.py
└── utils/
    └── helper.py
```

## 开发指南

### 代码结构

- `sync2txt.py`：主程序
- `directory_tree.py`：目录树生成模块
- `tests/`：单元测试

### 扩展建议

1. 添加更多文件类型支持
2. 实现增量更新模式
3. 支持远程存储输出

## 协议

MIT License
