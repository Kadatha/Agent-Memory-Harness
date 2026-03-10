import csv
with open('inventory.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
total_value = sum(float(row['price']) * float(row['quantity']) for row in rows)
print(total_value)