import json

# Load users.json from current directory
with open('users.json', 'r') as f:
    users = json.load(f)

# Load departments.json from current directory
with open('departments.json', 'r') as f:
    departments = json.load(f)

print("Users loaded:", users)
print("Departments loaded:", departments)

# Create a list of (department, age) pairs for all employees
department_max_age = {}
for user in users:
    dept = user['department']
    age = user['age']
    if dept not in department_max_age or age > department_max_age[dept]:
        department_max_age[dept] = age

print("Department max ages:", department_max_age)

# Find the oldest employee's department and age
oldest_dept = max(department_max_age, key=department_max_age.get)
oldest_age = department_max_age[oldest_dept]

print(f"Oldest employee is in: {oldest_dept}")
print(f"Age: {oldest_age}")