import json
with open('sales.json', 'r') as f:
    data = json.load(f)
highest_month = max(data, key=lambda x: x['revenue'])
total_revenue = sum(item['revenue'] for item in data)
print(f"Month with highest revenue: {highest_month['month']} ({highest_month['revenue']})")
print(f"Total revenue: {total_revenue}")