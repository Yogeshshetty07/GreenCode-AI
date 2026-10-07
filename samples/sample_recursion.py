# Uncached Exponential Recursion Sample (O(2^N) Carbon Heavy)
def fibonacci(n):
    # Lacks memoization decorator -> creates 2^N redundant function calls
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Execution trigger
result = fibonacci(28)
