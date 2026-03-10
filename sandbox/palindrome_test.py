s1 = 'A man a plan a canal Panama'
s2 = 'Hello World'
cleaned1 = s1.replace(' ', '').lower()
cleaned2 = s2.replace(' ', '').lower()
r1 = cleaned1 == cleaned1[::-1]
r2 = cleaned2 == cleaned2[::-1]
print(f'{r1}, {r2}')