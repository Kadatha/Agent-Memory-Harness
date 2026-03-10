def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = [num for num in range(30) if is_prime(num)]
print(f"Primes less than 30: {primes}")
total_sum = sum(primes)
print(f"Sum of primes less than 30: {total_sum}")