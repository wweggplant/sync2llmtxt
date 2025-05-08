# 简介

`sync2llmtxt` 是一个设计用来自动将指定目录中的源代码文件聚合到单个文本文件中的脚本。这有助于将整个项目代码作为上下文提供给大型语言模型（如 LLM/LLMtxt）。该脚本支持自动目录监控以实时更新聚合文档，也支持手动执行进行一次性生成。

中文 [English](README.md)
---

# 使用场景

你可以将目标文件指定为 Google Drive 中的目录，允许项目代码聚合到 Google Drive 中，便于与 Gemini 等一起使用。

## 主要特点

- **多文件类型支持**：聚合 `.py`、`.ts`、`.tsx`、`.js`、`.json`、`.md` 和其他常见代码和文本文件。
- **智能忽略**：
  - 自动应用 `.gitignore` 规则。
  - 支持自定义 `IGNORE_PATTERNS`。
  - 排除二进制文件、图像和其他不相关内容。
- **目录结构导出**：生成清晰的树形目录结构（包括忽略标记）。
- **灵活配置**：
  - 支持 YAML 配置文件。
  - 命令行参数覆盖。
- **高级过滤**：
  - 按文件大小过滤（`--max-size`）。
  - 按修改时间过滤（`--since-days`）。
- **详细日志**：多级日志记录用于调试。

## 安装方式

### 方式一：通过 PyPI 安装（推荐）

```bash
pip install sync2llmtxt
```

### 方式二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/sync2llmtxt.git
cd sync2llmtxt

# 开发模式安装
pip install -e .

# 安装开发依赖（可选）
pip install -r requirements-test.txt
```

### 配置

#### 1. 配置文件 (YAML)

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

| 参数 | 描述 | 示例 |
|------|------|------|
| `-s/--src` | 源代码目录 | `-s ./src` |
| `-o/--out` | 输出文件路径 | `-o output.txt` |
| `-c/--config` | 配置文件路径 | `-c config.yaml` |
| `--max-size` | 最大文件大小（MB） | `--max-size 2` |
| `--since-days` | 最近修改天数 | `--since-days 7` |

### 使用示例

```bash
# 基本用法
sync2llmtxt -s ./project -o output.txt

# 使用配置文件 + 过滤大文件
sync2llmtxt -c config.yaml --max-size 1.5

# 仅同步最近修改的文件
sync2llmtxt -s ./src -o out.txt --since-days 3
```

## 测试（待定）

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

- `src/sync2llmtxt/sync2llmtxt.py`：主程序。
- `src/sync2llmtxt/directory_tree.py`：目录树生成模块。
- `tests/`：单元测试。

### 扩展建议

1. 添加对更多文件类型的支持。
2. 实现增量更新模式。
3. 支持远程存储输出。

## 许可证

MIT 许可证
