with open('numbers.txt', 'r') as f:
    nums = [int(line) for line in f.readlines()]
total = sum(nums)
with open('sum.txt', 'w') as f:
    f.write(str(total))
print(f'Numbers read: {nums}')
print(f'Sum: {total}')