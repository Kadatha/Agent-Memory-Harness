#!/usr/bin/env python3
import json

# Generate first 10 Fibonacci numbers
fib = [0, 1]
for i in range(8):  # Need 8 more to get 10 total
    fib.append(fib[-1] + fib[-2])

print("Fibonacci numbers:", fib)
print("Sum:", sum(fib))

# Save as JSON list with newline for readability
with open('fibonacci.json', 'w') as f:
    json.dump([int(x) for x in fib], f, indent=2)}