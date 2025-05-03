from sync2txt import should_ignore, IGNORE_PATTERNS, setup_gitignore_parser

def test_should_ignore_patterns(tmp_path):
    (tmp_path / 'node_modules').mkdir()
    (tmp_path / 'main.py').write_text('print(1)')
    assert should_ignore(str(tmp_path / 'node_modules')) is True
    assert should_ignore(str(tmp_path / 'main.py')) is False

def test_should_ignore_gitignore(tmp_path):
    (tmp_path / '.gitignore').write_text('*.log\n')
    (tmp_path / 'a.log').write_text('log')
    (tmp_path / 'b.txt').write_text('txt')
    matcher = setup_gitignore_parser(tmp_path)
    assert matcher(str(tmp_path / 'a.log')) is True
    assert matcher(str(tmp_path / 'b.txt')) is False 