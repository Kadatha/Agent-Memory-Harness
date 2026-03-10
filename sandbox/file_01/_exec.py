with open('notes.txt', 'r') as f:
    content = f.read()
print(f"Total characters (including newlines): {len(content)}")
for i, line in enumerate(content.split('\n'), 1):
    print(f"Line {i}: '{line}' - length: {len(line) if i <= len(content.split(chr(10))) else 'N/A'}")