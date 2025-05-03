import os
from pathlib import Path
import logging

def generate_directory_structure(root_dir, should_ignore):
    """
    生成目录结构的字符串表示，忽略指定模式。
    参数：
        root_dir (str or Path): 根目录路径
        should_ignore (callable): 忽略判断函数，参数为绝对路径，返回bool
    返回：
        str: 目录结构树
    """
    structure_lines = []
    root_dir = Path(root_dir)
    structure_lines.append(f"{root_dir.name}/")

    def build_tree_recursive(current_dir, prefix, is_last_list):
        try:
            entries = sorted([e for e in current_dir.iterdir()])
        except Exception as e:
            logging.warning(f"Cannot list directory '{current_dir}': {e}")
            return
        filtered_entries = [e for e in entries if not should_ignore(str(e))]
        num_entries = len(filtered_entries)
        for i, entry in enumerate(filtered_entries):
            is_last_entry = (i == num_entries - 1)
            current_prefix_str = ''.join(["    " if last else "│   " for last in is_last_list])
            connector = "└── " if is_last_entry else "├── "
            display_name = entry.name + "/" if entry.is_dir() else entry.name
            structure_lines.append(f"{current_prefix_str}{connector}{display_name}")
            if entry.is_dir():
                build_tree_recursive(entry, prefix + ("    " if is_last_entry else "│   "), is_last_list + [is_last_entry])
    try:
        build_tree_recursive(root_dir, '', [])
    except Exception as e:
        logging.error(f"Error generating directory structure: {e}")
        return "*** Error generating directory structure ***"
    return "\n".join(structure_lines) + "\n" 