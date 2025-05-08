#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging

logger = logging.getLogger(__name__)

def generate_directory_structure(root_dir, should_ignore_fn=None):
    """
    生成目录结构的字符串表示，可选忽略特定路径
    
    参数:
        root_dir (str): 要生成结构的根目录
        should_ignore_fn (callable, optional): 一个函数，接收路径并返回布尔值决定是否忽略
        
    返回:
        str: 目录结构的字符串表示
    """
    structure_lines = []
    # Start with the root directory name
    structure_lines.append(os.path.basename(root_dir) + os.sep)

    def build_tree_recursive(current_dir, prefix, is_last_list):
        try:
            entries = sorted(os.listdir(current_dir))
        except OSError as e:
            logger.warning(f"Cannot list directory '{current_dir}' for tree structure: {e}")
            return # Stop traversing this branch

        # Filter entries based on ignore function if provided
        filtered_entries = []
        for entry in entries:
            full_path = os.path.join(current_dir, entry)
            if should_ignore_fn is None or not should_ignore_fn(full_path):
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
        # Filter root entries using should_ignore_fn
        filtered_root_entries = []
        for entry in root_entries:
            full_path = os.path.join(root_dir, entry)
            if should_ignore_fn is None or not should_ignore_fn(full_path):
                filtered_root_entries.append(entry)
            else:
                logger.debug(f"Skipping root entry: '{full_path}' (ignored by should_ignore)")
                
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

if __name__ == "__main__":
    # Simple test
    import sys
    if len(sys.argv) > 1:
        print(generate_directory_structure(sys.argv[1]))
    else:
        print(generate_directory_structure(".")) 