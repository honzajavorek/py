import json
from pathlib import Path

import yaml

from . import build


builder_path = Path(__file__).parent

config_path = builder_path / 'config.yml'
config = yaml.safe_load(config_path.read_text())

data = build(config)

data_path = builder_path / 'data.json'
data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
