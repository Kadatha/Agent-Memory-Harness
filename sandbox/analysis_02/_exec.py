import random
import json
from collections import Counter

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

random.seed(42)
n = [random.randint(1, 1000) for _ in range(100)]
with open('numbers.json', 'w') as f:
    json.dump(n, f)
mean_val = sum(n)/len(n)
sorted_n = sorted(n)
mid = len(sorted_n)//2
if mid == 0 or (mid + 1) >= len(sorted_n):
    median_val = sorted_n[mid]
else:
    median_val = (sorted_n[mid-1] + sorted_n[mid]) / 2
tens_digits = [(x // 10) % 10 for x in n]
counter_tens = Counter(tens_digits)
modes_tens = counter_tens.most_common()
mode_most_frequent_digit = modes_tens[0][0] if len(modes_tens) > 0 else None
prime_count = sum(1 for x in n if is_prime(x))
print(f"Mean: {mean_val}")
print(f"Median: {median_val}")
print(f"Mode (tens digit): {mode_most_frequent_digit} (appears {counter_tens[mode_most_frequent_digit]} times)")
print(f"Prime count: {prime_count}")