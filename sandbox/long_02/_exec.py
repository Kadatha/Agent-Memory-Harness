with open('log.txt', 'w') as f:
    f.write('Step 1: initialized\n')

for step in range(2, 7):
    with open('log.txt', 'r') as f:
        lines = [line for line in f.readlines() if line.strip()]
        count = len(lines)
    with open('log.txt', 'a') as f:
        f.write(f'Step {step}: count was {count}\n')

with open('log.txt', 'r') as f:
    final_lines = [line for line in f.readlines() if line.strip()]
    print(len(final_lines))