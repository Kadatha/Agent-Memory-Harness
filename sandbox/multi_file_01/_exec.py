with open('part1.txt', 'r') as f:
    content = f.read()

with open('part2.txt', 'r') as f:
    content += f.read()

with open('part3.txt', 'r') as f:
    content += f.read()

with open('combined.txt', 'w') as f:
    f.write(content)
print(content)