def safe_divide(a, b):
    if b == 0:
        return 'infinity'
    result = a / b
    return result

# Case 1: divide 10 by 3 (float division)
r1 = safe_divide(10, 3)
print(f"Case 1 - 10/3 = {r1}")

# Case 2: divide 10 by 0
r2 = safe_divide(10, 0)
print(f"Case 2 - 10/0 = {r2}")

# Case 3: divide 0 by 10
r3 = safe_divide(0, 10)
print(f"Case 3 - 0/10 = {r3}")