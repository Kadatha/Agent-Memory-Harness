import json

# Generate first 10 Fibonacci numbers
fib = [0, 1]
for i in range(8):  # Need 8 more to get 10 total
    fib.append(fib[-1] + fib[-2])

print('First 10 Fibonacci numbers:', fib)
with open('fibonacci.json', 'w') as f:
    json.dump(fib, f)

# Read back and sum
with open('fibonacci.json', 'r') as f:
    loaded_fib = json.load(f)

total_sum = sum(loaded_fib)
print('Sum of all 10 numbers:', total_sum)