import json
import os

# Get the root directory of the project (assuming this file is in asociety/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    configuration = json.load(f)
