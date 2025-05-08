import yaml
from sync2llmtxt import load_config

def test_load_config(tmp_path):
    config_path = tmp_path / 'config.yaml'
    config_data = {
        'MONITORED_CODE_DIR': '/test/dir',
        'OUTPUT_DOCUMENT_PATH': '/test/out.txt',
        'CODE_FILE_PATTERNS': ['*.py'],
        'IGNORE_PATTERNS': ['node_modules'],
        'ENABLE_AUTOMATIC_MONITORING': False,
        'DEBOUNCE_TIME': 2.0
    }
    config_path.write_text(yaml.dump(config_data))
    config = load_config(str(config_path))
    assert config['MONITORED_CODE_DIR'] == '/test/dir'
    assert config['CODE_FILE_PATTERNS'] == ['*.py'] 