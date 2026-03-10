def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

two_digit_primes = []
for num in range(10, 100):
    digit_sum = sum(int(d) for d in str(num))
    if is_prime(num) and digit_sum == 10:
        two_digit_primes.append(num)

print(two_digit_primes)
