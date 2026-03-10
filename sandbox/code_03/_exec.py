def is_palindrome(s):
    # Remove spaces and convert to lowercase
    cleaned = s.replace(' ', '').lower()
    return cleaned == cleaned[::-1]

# Test cases
test1 = 'A man a plan a canal Panama'
test2 = 'Hello World'
result1 = is_palindrome(test1)
result2 = is_palindrome(test2)
print(f'{test1}: {result1}')
print(f'{test2}: {result2}')