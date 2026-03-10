arr = [64, 34, 25, 12, 22, 11, 90]
log_lines = []
n = len(arr)
passes = 0
i = 0
while i < n - 1:
    swapped = False
    for j in range(n - 1 - i):
        if arr[j] > arr[j + 1]:
            arr[j], arr[j + 1] = arr[j + 1], arr[j]
            swapped = True
    passes += 1
    log_lines.append(str(arr))
    print(f"Pass {passes}: {' '.join(map(str, arr))}")
    i += 1
print()
with open('sort_log.txt', 'w') as f:
    for line in log_lines:
        f.write(line + '\n')
print("Sorted list:", arr)
print("Total passes:", len(log_lines))