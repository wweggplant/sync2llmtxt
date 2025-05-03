from directory_tree import generate_directory_structure

def test_generate_directory_structure_simple(tmp_path):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'a' / 'b.txt').write_text('hi')
    tree = generate_directory_structure(tmp_path, lambda p: False)
    assert 'a/' in tree and 'b.txt' in tree

def test_generate_directory_structure_ignore(tmp_path):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'a' / 'b.txt').write_text('hi')
    tree = generate_directory_structure(tmp_path, lambda p: 'b.txt' in p)
    assert 'b.txt' not in tree 