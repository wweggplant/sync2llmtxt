#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import sys
import glob
import logging
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import throttle
import argparse
import yaml
from gitignore_parser import parse_gitignore
from pathlib import Path
from directory_tree import generate_directory_structure

# --- 配置区 ---
# (Configuration remains the same as your last version)
# 1. 监控目录
MONITORED_CODE_DIR = '/path/to/your/code'  # 请根据实际项目路径修改
# 2. 包含的文件类型
CODE_FILE_PATTERNS = [
    # 脚本语言
    '*.py', '*.rb', '*.pl', '*.php', '*.lua', '*.groovy',
    # JVM 生态
    '*.java', '*.kt', '*.scala', '*.clj',  # Java/Kotlin/Scala/Clojure
    # Web开发
    '*.html', '*.htm', '*.css', '*.scss', '*.less',
    '*.js', '*.mjs', '*.ts', '*.tsx', '*.jsx', '*.vue', '*.svelte',
    # 编译型语言
    '*.c', '*.cpp', '*.h', '*.hpp', '*.cc', '*.hh',
    '*.go', '*.rs', '*.swift', '*.dart', '*.zig',
    # 函数式语言
    '*.hs', '*.elm', '*.erl', '*.ex', '*.exs',  # Haskell/Elm/Erlang/Elixir
    # 配置文件
    '*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.cfg', '*.env',
    # 数据库
    '*.sql', '*.prisma', '*.edgeql', '*.psql',
    # 文档
    '*.md', '*.rst', '*.tex', '*.org', '*.adoc',  # Markdown/reST/LaTeX/Org/AsciiDoc
    # 构建/脚本
    'Makefile', 'CMakeLists.txt', '*.mk', '*.sh', '*.bash', '*.zsh', '*.bat', '*.ps1',
    # 基础设施
    '*.tf', '*.hcl',  # Terraform
    '*.dockerfile', 'Dockerfile', '*.containerfile',
    # 其他
    '*.xml', '*.csv', '*.proto', '*.thrift'  # 协议文件
]
# 3. 输出文档路径
OUTPUT_DOCUMENT_PATH = '/path/to/your/output.txt'  # 请根据实际需求修改输出文件路径
# 4. 忽略模式
IGNORE_PATTERNS = [
    'node_modules', '.git', '__pycache__', 'venv', '.venv', 'env',
    '.vscode', '.idea', 'build', 'dist', '.next', 'shared/generated',
    'shared/prisma/prisma/dev.db', '.DS_Store', '.mypy_cache',
    '.pytest_cache', '.ruff_cache', '*.pyc', '*.swp', '*~', '*.log',
    '*.db', '*.sqlite', '*.sqlite3', '*.node', '*.so', '*.dll', '*.dylib',
    '*.gz', '*.zip', '*.tar', '*.rar', '*.png', '*.jpg', '*.jpeg', '*.gif',
    '*.svg', '*.ico', '*.mp4', '*.mov', '*.avi', '*.pdf',
]
# 5. 防抖时间
DEBOUNCE_TIME = 2.0
# 6. 运行模式
ENABLE_AUTOMATIC_MONITORING = True
# --- /配置区 ---

# --- Logging Setup ---
logger = logging.getLogger(__name__)
# --- /Logging Setup ---

# 新增：配置文件加载函数
def load_config(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return None

# 新增：gitignore解析器（全局变量）
gitignore_matcher = None

def setup_gitignore_parser(root_dir):
    gitignore_path = os.path.join(root_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        try:
            return parse_gitignore(gitignore_path)
        except Exception as e:
            logger.warning(f"解析 .gitignore 失败: {e}")
    return None

def setup_logging():
    """Configures logging to file and console."""
    log_filename = 'sync_script.log'
    log_level_file = logging.DEBUG # Capture everything in the file
    log_level_console = logging.INFO # Show INFO and above on console

    # Create logger
    _logger = logging.getLogger('') # Get root logger
    _logger.setLevel(log_level_file) # Set overall level to lowest (DEBUG)

    # File Handler (DEBUG level)
    try:
        file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8') # Overwrite log each run
        file_handler.setLevel(log_level_file)
        file_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        _logger.addHandler(file_handler)
    except Exception as e:
        print(f"FATAL: Could not configure file logging to {log_filename}: {e}", file=sys.stderr)
        # Fallback to console logging only if file logging fails
        logging.basicConfig(level=log_level_console, format='[%(levelname)-8s] %(message)s')
        return

    # Console Handler (INFO level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level_console)
    console_formatter = logging.Formatter('[%(levelname)-8s] %(message)s') # Simpler format
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    logger.info(f"Logging initialized. DEBUG level logs going to '{log_filename}'.")


def should_ignore(path):
    """检查路径是否应该被忽略 (用于文件内容聚合和目录结构生成)"""
    normalized_path = os.path.normpath(path)
    filename = os.path.basename(normalized_path)

    # If the path itself is the monitored directory, never ignore it.
    if normalized_path == os.path.normpath(MONITORED_CODE_DIR):
        return False

    # 获取相对于监控目录的路径，用于更可靠的检查
    try:
        relative_path = os.path.relpath(normalized_path, MONITORED_CODE_DIR)
    except ValueError:
        # 如果路径不在监控目录下（例如奇怪的符号链接），可能直接忽略或基于绝对路径判断
        # For tree generation, paths must be within the root, so this case might indicate an issue,
        # but the path checks below should still handle it if the pattern matches.
        relative_path = None

    # 绝对路径的各部分
    parts = normalized_path.split(os.sep)

    # 优先用 gitignore_matcher
    if gitignore_matcher and gitignore_matcher(path):
        return True

    for pattern in IGNORE_PATTERNS:
        reason = ""
        is_wildcard_suffix = pattern.startswith('*') and not os.sep in pattern
        contains_separator = os.sep in pattern or '/' in pattern # Check both separators for robustness

        # Case 1: Wildcard Suffix (e.g., *.log) - Checks only the filename
        if is_wildcard_suffix:
            if filename.endswith(pattern[1:]):
                reason = f"Suffix pattern '{pattern}'"
                # logger.debug(f"IGNORE: Path='{normalized_path}' Reason='{reason}'") # Keep logging out of should_ignore for cleaner structure generation
                return True
        # Case 2: Pattern contains separator (e.g., shared/generated, node_modules)
        # Checks if the normalized path *contains* the pattern as a distinct path segment.
        elif contains_separator:
            # 规范化模式中的分隔符，以匹配当前操作系统
            normalized_pattern = os.path.normpath(pattern)
            # Add separators around pattern to ensure matching full directory/path segments
            pattern_check_absolute = f"{os.sep}{normalized_pattern}{os.sep}"
            # Add separators around path
            path_check_absolute = f"{os.sep}{normalized_path}{os.sep}"

            if pattern_check_absolute in path_check_absolute:
                reason = f"Path segment pattern '{normalized_pattern}' in absolute path"
                # logger.debug(f"IGNORE: Path='{normalized_path}' Reason='{reason}'")
                return True

            # Check if the relative path starts with the pattern (important for things like 'shared/generated')
            if relative_path is not None:
                pattern_start = f"{normalized_pattern}{os.sep}"
                if relative_path.startswith(pattern_start):
                     reason = f"Relative path start pattern '{normalized_pattern}'"
                     # logger.debug(f"IGNORE: Path='{normalized_path}' Reason='{reason}'")
                     return True
                # Also check for exact relative path match
                if relative_path == normalized_pattern:
                    reason = f"Relative path exact match pattern '{normalized_pattern}'"
                    # logger.debug(f"IGNORE: Path='{normalized_path}' Reason='{reason}'")
                    return True


        # Case 3: Simple name (no wildcard, no separator, e.g., .git)
        # Checks if any part of the absolute path matches the simple name.
        elif not '*' in pattern:
            if pattern in parts:
                reason = f"Simple name part '{pattern}'"
                # logger.debug(f"IGNORE: Path='{normalized_path}' Reason='{reason}'")
                return True

    # If no pattern matched
    return False

def generate_directory_structure(root_dir):
    """生成目录结构的字符串表示，忽略指定模式"""
    structure_lines = []
    # Start with the root directory name
    structure_lines.append(os.path.basename(root_dir) + os.sep)

    def build_tree_recursive(current_dir, prefix, is_last_list):
        try:
            entries = sorted(os.listdir(current_dir))
        except OSError as e:
            logger.warning(f"Cannot list directory '{current_dir}' for tree structure: {e}")
            # Indicate error in tree if possible? Or just return. Let's just return.
            # structure_lines.append(f"{prefix}[Error listing directory]")
            return # Stop traversing this branch

        # Filter entries based on ignore patterns
        filtered_entries = []
        for entry in entries:
            full_path = os.path.join(current_dir, entry)
            if not should_ignore(full_path):
                 filtered_entries.append(entry)
            else:
                 logger.debug(f"Skipping tree entry: '{full_path}' (ignored by should_ignore)")


        num_entries = len(filtered_entries)
        for i, entry in enumerate(filtered_entries):
            is_last_entry = (i == num_entries - 1)
            full_path = os.path.join(current_dir, entry)

            # Build the prefix string based on the is_last_list state
            current_prefix_str = ""
            for is_last_parent in is_last_list:
                current_prefix_str += "    " if is_last_parent else "│   "

            connector = "└── " if is_last_entry else "├── "

            display_name = entry
            if os.path.isdir(full_path):
                 display_name += os.sep # Add a slash to directory names in the tree

            structure_lines.append(f"{current_prefix_str}{connector}{display_name}")

            if os.path.isdir(full_path):
                # Recursively call for subdirectories
                # Pass updated prefix and append current entry's last status to the list
                build_tree_recursive(full_path, prefix + ("    " if is_last_entry else "│   "), is_last_list + [is_last_entry])

    # Start the recursive process for the children of the root directory
    try:
        root_entries = sorted(os.listdir(root_dir))
        # Filter root entries using should_ignore
        filtered_root_entries = [
            entry for entry in root_entries
            if not should_ignore(os.path.join(root_dir, entry))
        ]
        num_root_entries = len(filtered_root_entries)

        for i, entry in enumerate(filtered_root_entries):
            is_last_entry = (i == num_root_entries - 1)
            full_path = os.path.join(root_dir, entry)

            connector = "└── " if is_last_entry else "├── "
            display_name = entry
            if os.path.isdir(full_path):
                 display_name += os.sep

            structure_lines.append(f"{connector}{display_name}")

            if os.path.isdir(full_path):
                 # Start recursive call for subdirectories, initial is_last_list contains only the status of this entry
                 build_tree_recursive(full_path, ("    " if is_last_entry else "│   "), [is_last_entry])

    except OSError as e:
        logger.error(f"FATAL: Cannot list root directory '{root_dir}' to generate tree structure: {e}")
        return "*** Error generating directory structure ***" # Return an error message

    return "\n".join(structure_lines)


@throttle.wrap(20, 1)  # 20秒内只允许1次
def aggregate_code_to_document(is_manual_run=False, max_file_size_warn=1*1024*1024, since_timestamp=None):
    """聚合指定目录和类型的文件内容到目标文档，并添加目录结构"""
    logger.info(f"开始聚合代码到 {OUTPUT_DOCUMENT_PATH}...")
    all_code_content = []
    included_files_log = []
    error_files_log = []
    total_size_bytes = 0

    source_path = Path(MONITORED_CODE_DIR)
    files_to_process = []
    for pattern in CODE_FILE_PATTERNS:
        files_to_process.extend(source_path.rglob(pattern))
    unique_files = sorted(list(set(files_to_process)), key=lambda p: str(p))
    logger.info(f"找到 {len(unique_files)} 个唯一文件路径。开始过滤和处理文件内容...")

    processed_count = 0
    ignored_count = 0
    included_count = 0

    for file_path in unique_files:
        processed_count += 1
        if not file_path.is_file():
            continue
        if should_ignore(str(file_path)):
            logger.debug(f"Ignoring file based on pattern: '{file_path}'")
            ignored_count += 1
            continue
        if since_timestamp is not None:
            mtime = file_path.stat().st_mtime
            if mtime < since_timestamp:
                logger.debug(f"文件 '{file_path}' 修改时间早于 since-days，跳过。")
                ignored_count += 1
                continue
        relative_path = str(file_path.relative_to(MONITORED_CODE_DIR))
        try:
            file_size = file_path.stat().st_size
            if file_size > max_file_size_warn:
                logger.warning(f"跳过大文件: '{relative_path}' (大小: {file_size / (1024*1024):.2f} MB > {max_file_size_warn / (1024*1024):.2f} MB)")
                included_files_log.append(relative_path + f" (Too Large: {file_size / (1024*1024):.2f} MB)")
                ignored_count += 1
                continue
            if file_size == 0:
                logger.info(f"文件 '{relative_path}' 为空，跳过内容。")
                included_files_log.append(relative_path + " (Empty)")
                included_count += 1
                continue
            with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            included_files_log.append(relative_path)
            all_code_content.append(f"\n--- File: {relative_path} ---\n\n{content}\n")
            total_size_bytes += file_size
            included_count += 1
        except Exception as read_err:
            logger.error(f"无法读取文件 '{file_path}': {read_err}")
            error_files_log.append(relative_path + f" (Read Error: {read_err})")

    logger.info(f"文件内容处理完成。总路径: {processed_count}, 已忽略: {ignored_count}, 尝试包含: {included_count}, 读取错误: {len(error_files_log)}.")

    # --- 准备最终内容 ---
    mode_text = "Manual Run" if is_manual_run or not ENABLE_AUTOMATIC_MONITORING else "Auto Update"
    final_content = f"--- Project Code Context ({mode_text} @ {time.strftime('%Y-%m-%d %H:%M:%S')}) ---\n\n"

    # --- 文件列表 ---
    if not included_files_log and not error_files_log:
        final_content += "*** No matching code files found or all were ignored. ***\n"
        logger.warning("未找到任何可包含的文件。")
    else:
        final_content += f"Included Files ({len(included_files_log)}):\n"
        all_listed_files = sorted(included_files_log + error_files_log)
        for fname in all_listed_files:
            status = ""
            if " (Empty)" in fname: status = " (Empty)"
            elif " (OS Error" in fname: status = " (OS Error)"
            elif " (Read Error)" in fname: status = " (Read Error)"
            elif " (Unknown Error)" in fname: status = " (Unknown Error)"
            display_name = fname.split(" (")[0]
            final_content += f"- {display_name}{status}\n"
        final_content += "\n---\n\n"

    # --- 代码内容 ---
    final_content += "".join(all_code_content)

    # --- 添加目录结构 ---
    logger.info("Generating directory structure...")
    try:
        dir_structure = generate_directory_structure(MONITORED_CODE_DIR)
        final_content += "\n\n---\n\n" # Separator before structure
        final_content += "--- Directory Structure (Ignoring Patterns) ---\n\n"
        final_content += dir_structure
        final_content += "\n\n--- End of Document ---"
        logger.info("Directory structure generated and added.")
    except Exception as e:
        logger.error(f"Error generating directory structure: {e}")
        final_content += "\n\n---\n\n"
        final_content += "--- Directory Structure ---\n\n"
        final_content += "*** Failed to generate directory structure ***"
        final_content += "\n\n--- End of Document ---"


    # --- 写入文件 ---
    logger.info(f"准备写入文档，包含 {len(included_files_log)} 个文件的内容，总源文件大小约 {total_size_bytes / (1024):.2f} KB。")
    write_successful = False
    try:
        output_dir = os.path.dirname(OUTPUT_DOCUMENT_PATH)
        if not os.path.exists(output_dir):
             logger.info(f"输出目录不存在，尝试创建: {output_dir}")
             os.makedirs(output_dir)
        logger.info(f"尝试写入文件到: {OUTPUT_DOCUMENT_PATH}")
        with open(OUTPUT_DOCUMENT_PATH, 'w', encoding='utf-8') as f:
            bytes_written = f.write(final_content)
        logger.info(f"文件写入操作调用完成 (报告写入 {bytes_written} 个字符)。")
        write_successful = True
        logger.info(f"代码和目录结构已聚合更新到 {OUTPUT_DOCUMENT_PATH}")
    except Exception as e:
        logger.error(f"写入输出文件时发生异常 {OUTPUT_DOCUMENT_PATH}: {e}")

    # --- 写入后立即检查文件 ---
    logger.debug("POST-WRITE CHECK: 脚本执行后，立即验证文件...")
    try:
        time.sleep(0.5) # Short delay for filesystem
        if os.path.exists(OUTPUT_DOCUMENT_PATH):
            final_size = os.path.getsize(OUTPUT_DOCUMENT_PATH)
            logger.debug(f"POST-WRITE CHECK: File '{OUTPUT_DOCUMENT_PATH}' EXISTS. Size: {final_size} bytes.")
        else:
            logger.error(f"POST-WRITE CHECK: File '{OUTPUT_DOCUMENT_PATH}' 在写入操作后未能找到！")
            if write_successful:
                 logger.error("POST-WRITE CHECK: 这表明脚本认为写入成功，但文件系统没有文件。检查路径、权限或可能的外部干扰。")

    except Exception as e:
        logger.error(f"POST-WRITE CHECK: 检查文件时发生错误: {e}")


# --- CodeChangeHandler (仅在自动模式下使用) ---
class CodeChangeHandler(FileSystemEventHandler):
     def on_any_event(self, event):
         # Only process events for files, and only if monitoring is enabled
         if not ENABLE_AUTOMATIC_MONITORING or event.is_directory:
             return

         # 只处理文件被修改或新建的事件
         if event.event_type not in ('modified', 'created', 'deleted'):
             logger.debug(f"Event type '{event.event_type}' ignored for path: '{event.src_path}'")
             return

         normalized_path = os.path.normpath(event.src_path)

         logger.debug(f"Event received: Type='{event.event_type}', Path='{normalized_path}', IsDir={event.is_directory}")

         # Use should_ignore to filter out ignored files/paths BEFORE checking file patterns
         if should_ignore(normalized_path):
              logger.debug(f"Ignoring event for path based on ignore patterns: '{normalized_path}'")
              return

         filename = os.path.basename(normalized_path)
         matches_pattern = False
         for pattern in CODE_FILE_PATTERNS:
              # Simple direct match or wildcard match (like *.py)
              if pattern == filename or (pattern.startswith('*') and filename.endswith(pattern[1:])):
                  matches_pattern = True
                  break

         if matches_pattern:
              logger.debug(f"Relevant event detected for '{normalized_path}'. Triggering aggregation function...")
              aggregate_code_to_document(is_manual_run=False)
         else:
             logger.debug(f"Event path '{normalized_path}' does not match code file patterns.")


# --- 主执行块 (__main__) ---
if __name__ == "__main__":
    # --- Setup Logging FIRST ---
    setup_logging() # Initialize logging to file and console

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="聚合指定目录下的代码文件到单一文本文件，便于大模型处理。")
    parser.add_argument('-s', '--src', type=str, default=MONITORED_CODE_DIR, help='需要聚合的源代码目录')
    parser.add_argument('-o', '--out', type=str, default=OUTPUT_DOCUMENT_PATH, help='输出的聚合文档路径')
    parser.add_argument('-c', '--config', type=str, default=None, help='配置文件路径 (YAML)')
    parser.add_argument('--max-size', type=float, default=1.0, help='最大单文件体积（MB），超过则跳过，默认1MB')
    parser.add_argument('--since-days', type=int, default=None, help='只聚合最近N天内修改的文件')
    args = parser.parse_args()

    # 加载配置文件（如有）
    if args.config:
        config = load_config(args.config)
        if config:
            MONITORED_CODE_DIR = config.get('MONITORED_CODE_DIR', MONITORED_CODE_DIR)
            OUTPUT_DOCUMENT_PATH = config.get('OUTPUT_DOCUMENT_PATH', OUTPUT_DOCUMENT_PATH)
            CODE_FILE_PATTERNS = config.get('CODE_FILE_PATTERNS', CODE_FILE_PATTERNS)
            IGNORE_PATTERNS = config.get('IGNORE_PATTERNS', IGNORE_PATTERNS)
            ENABLE_AUTOMATIC_MONITORING = config.get('ENABLE_AUTOMATIC_MONITORING', ENABLE_AUTOMATIC_MONITORING)
            DEBOUNCE_TIME = config.get('DEBOUNCE_TIME', DEBOUNCE_TIME)

    # 命令行参数覆盖
    MONITORED_CODE_DIR = os.path.abspath(args.src)
    OUTPUT_DOCUMENT_PATH = os.path.abspath(args.out)

    # --- Initial Setup & Validation ---
    try:
        MONITORED_CODE_DIR = os.path.abspath(MONITORED_CODE_DIR)
        OUTPUT_DOCUMENT_PATH = os.path.abspath(OUTPUT_DOCUMENT_PATH)
    except Exception as e:
        logger.critical(f"配置的路径无效: {e}") # Use CRITICAL for fatal errors
        sys.exit(1)

    # 初始化 gitignore 解析器
    gitignore_matcher = setup_gitignore_parser(MONITORED_CODE_DIR)

    logger.info("--- 代码和目录结构打包脚本 ---")
    logger.info(f"模式: {'自动监控' if ENABLE_AUTOMATIC_MONITORING else '手动运行'}")
    logger.info(f"监控/源目录: {MONITORED_CODE_DIR}")
    logger.info(f"目标文档: {OUTPUT_DOCUMENT_PATH}")
    logger.info(f"监控文件类型: {', '.join(CODE_FILE_PATTERNS)}")
    logger.info(f"忽略模式数量: {len(IGNORE_PATTERNS)}") # Log count instead of full list to console
    logger.debug(f"忽略模式列表: {', '.join(IGNORE_PATTERNS)}") # Full list in debug log
    if ENABLE_AUTOMATIC_MONITORING:
        logger.info(f"防抖时间: {DEBOUNCE_TIME} 秒")
    logger.info("-------------------------")

    if not os.path.isdir(MONITORED_CODE_DIR):
         logger.critical(f"源目录 '{MONITORED_CODE_DIR}' 无效。")
         sys.exit(1)

    # --- Core Execution ---
    logger.info("正在执行初始/手动文档生成/更新...")
    max_file_size_warn = int(args.max_size * 1024 * 1024)
    since_days = args.since_days
    since_timestamp = None
    if since_days is not None:
        since_timestamp = time.time() - since_days * 86400
    aggregate_code_to_document(is_manual_run=not ENABLE_AUTOMATIC_MONITORING, max_file_size_warn=max_file_size_warn, since_timestamp=since_timestamp)

    # --- Start Monitoring (if auto mode) ---
    if ENABLE_AUTOMATIC_MONITORING:
        logger.info("自动监控模式已启用...")
        try:
            event_handler = CodeChangeHandler()
            observer = Observer()
            # Watchdog's ignore patterns are less flexible than our should_ignore.
            # We will rely on should_ignore within the handler, but telling watchdog
            # to ignore common large directories like node_modules can improve performance.
            # However, implementing watchdog ignores needs careful consideration to not conflict
            # with our pattern matching. For simplicity and robustness, we'll let watchdog notify
            # for ignored paths and filter them *within* our handler using should_ignore.
            observer.schedule(event_handler, MONITORED_CODE_DIR, recursive=True)
            logger.info("监控器设置成功。")
        except Exception as e:
             logger.critical(f"无法启动监控器: {e}")
             logger.critical("请确保 'watchdog' 库已安装 (pip install watchdog) 并且路径权限正确。")
             sys.exit(1)

        logger.info("监控已启动。按 Ctrl+C 停止脚本。")
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("检测到 Ctrl+C，正在停止监控...")
        observer.join()
        logger.info("监控已成功停止。")
        logger.info("脚本退出 (自动模式)。")
    else:
        logger.info("脚本执行完毕 (手动模式)。")
        # Give logs a moment to flush before exiting
        logging.shutdown()
        time.sleep(0.1)
        sys.exit(0)