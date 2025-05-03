import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

@pytest.fixture
def sample_tree(tmp_path):
    # 创建如下结构
    # root/
    #   main.py
    #   node_modules/
    #   .git/
    #   docs/readme.md
    (tmp_path / 'main.py').write_text('print(1)')
    (tmp_path / 'node_modules').mkdir()
    (tmp_path / '.git').mkdir()
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs' / 'readme.md').write_text('# doc')
    return tmp_path 