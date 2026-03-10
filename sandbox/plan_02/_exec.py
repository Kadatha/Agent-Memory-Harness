import json

with open('todo.json', 'r') as f:
    todos = json.load(f)

incomplete_count = sum(1 for t in todos if not t['done'])
print(f"Incomplete tasks count: {incomplete_count}")