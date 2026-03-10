import json

# Read from fibonacci.json
with open('fibonacci.json', 'r') as f:
    fib = json.load(f)

print("Fibonacci numbers loaded:", fib)
sum_fib = sum(fib)
print("Sum of all 10 Fibonacci numbers:", sum_fib)