def is_palindrome(s):
    cleaned = s.replace(' ', '').lower()
    return cleaned == cleaned[::-1]

result1 = is_palindrome('A man a plan a canal Panama')
result2 = is_palindrome('Hello World')
print(f"{result1}, {result2}")