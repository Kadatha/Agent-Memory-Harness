sales = [32456, 28791, 35678, 41234, 38901, 33567, 45678, 42890, 36789, 39456, 41234, 48567]
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
avg = sum(sales)/len(sales)
stdev_val = (sum((x-avg)**2 for x in sales) / len(sales))**0.5
best_idx = max(range(len(sales)), key=lambda i: sales[i])
worst_idx = min(range(len(sales)), key=lambda i: sales[i])
print(f"Best month: {months[best_idx]} - Sales: {sales[best_idx]}")
print(f"Worst month: {months[worst_idx]} - Sales: {sales[worst_idx]}")
print(f"Average: {round(avg, 2)}")
print(f"Standard Deviation: {round(stdev_val, 2)}")