import json
from collections import deque
def fibonacci(n):
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:10]
fib_numbers = fibonacci(10)
data = {'fibonacci': fib_numbers}
with open('fibonacci.json', 'w') as f:
    json.dump(data, f)
print(sum(fib_numbers))