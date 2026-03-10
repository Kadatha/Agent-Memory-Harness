import json
with open('config.json', 'r') as f:
    config = json.load(f)
print(config['max_retries'])