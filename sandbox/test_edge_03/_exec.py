def safe_divide(a, b):
    if b == 0:
        return "infinity"
    else:
        return a / b

result1 = safe_divide(10, 3)
result2 = safe_divide(10, 0)
result3 = safe_divide(0, 10)

print(f"10/3: {result1}")
print(f"10/0: {result2}")
print(f"0/10: {result3}")