import json
with open('fibonacci.json', 'r') as f:
    fibonacci = json.load(f)
sum_fib = sum(fibonacci)
print("Fibonacci numbers from file:", fibonacci)
print("Sum of all 10 Fibonacci numbers:", sum_fib)