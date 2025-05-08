import sys
import os
import time
from sync2llmtxt import aggregate_code_to_document

def test_aggregate_code_to_document(tmp_path):
    # 创建小文件和大文件
    small = tmp_path / 'small.py'
    big = tmp_path / 'big.py'
    small.write_text('x=1')
    big.write_bytes(b'x' * 2 * 1024 * 1024)  # 2MB
    out_file = tmp_path / 'out.txt'
    sys.modules['sync2llmtxt'].MONITORED_CODE_DIR = str(tmp_path)
    sys.modules['sync2llmtxt'].OUTPUT_DOCUMENT_PATH = str(out_file)
    aggregate_code_to_document(is_manual_run=True, max_file_size_warn=1*1024*1024)
    content = out_file.read_text()
    assert 'small.py' in content
    assert 'big.py' not in content

def test_aggregate_code_to_document_since_days(tmp_path):
    old = tmp_path / 'old.py'
    new = tmp_path / 'new.py'
    old.write_text('old')
    new.write_text('new')
    old_mtime = time.time() - 10 * 86400
    os.utime(old, (old_mtime, old_mtime))
    out_file = tmp_path / 'out.txt'
    sys.modules['sync2llmtxt'].MONITORED_CODE_DIR = str(tmp_path)
    sys.modules['sync2llmtxt'].OUTPUT_DOCUMENT_PATH = str(out_file)
    aggregate_code_to_document(is_manual_run=True, max_file_size_warn=1*1024*1024, since_timestamp=time.time() - 7*86400)
    content = out_file.read_text()
    assert 'new.py' in content
    assert 'old.py' not in content 