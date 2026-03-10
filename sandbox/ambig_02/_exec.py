temps_c = [20, 25, 30, 15, 35]
# Convert Celsius to Fahrenheit
f_temps = [(c * 9/5 + 32) for c in temps_c]
print('Fahrenheit values:', f_temps)
avg_f = sum(f_temps) / len(f_temps)
print('Average Fahrenheit:', avg_f)
avg_c = (avg_f - 32) * 5/9
print('Back to Celsius:', round(avg_c, 1))