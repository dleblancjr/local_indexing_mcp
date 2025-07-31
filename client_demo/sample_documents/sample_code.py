#!/usr/bin/env python3
"""
Sample Python code demonstrating basic programming concepts.

This file contains examples of:
- Functions
- Classes
- Data structures
- Control flow
- Error handling
"""

import math
import random
from typing import List, Dict, Optional


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using recursion.
    
    Args:
        n: The position in the Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_iterative(n: int) -> int:
    """
    Calculate the nth Fibonacci number iteratively (more efficient).
    
    Args:
        n: The position in the Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


class Calculator:
    """A simple calculator class demonstrating object-oriented programming."""
    
    def __init__(self):
        """Initialize the calculator with an empty history."""
        self.history: List[str] = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero!")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def get_history(self) -> List[str]:
        """Get the calculation history."""
        return self.history.copy()
    
    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history.clear()


class DataProcessor:
    """Example class for data processing operations."""
    
    @staticmethod
    def filter_even_numbers(numbers: List[int]) -> List[int]:
        """Filter out even numbers from a list."""
        return [num for num in numbers if num % 2 == 0]
    
    @staticmethod
    def calculate_statistics(numbers: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a list of numbers."""
        if not numbers:
            return {}
        
        return {
            'count': len(numbers),
            'sum': sum(numbers),
            'mean': sum(numbers) / len(numbers),
            'min': min(numbers),
            'max': max(numbers),
            'range': max(numbers) - min(numbers)
        }
    
    @staticmethod
    def find_prime_numbers(limit: int) -> List[int]:
        """Find all prime numbers up to a given limit using Sieve of Eratosthenes."""
        if limit < 2:
            return []
        
        # Initialize sieve
        sieve = [True] * (limit + 1)
        sieve[0] = sieve[1] = False
        
        # Mark multiples as non-prime
        for i in range(2, int(math.sqrt(limit)) + 1):
            if sieve[i]:
                for j in range(i * i, limit + 1, i):
                    sieve[j] = False
        
        # Collect prime numbers
        return [i for i in range(2, limit + 1) if sieve[i]]


def demonstrate_error_handling():
    """Demonstrate proper error handling in Python."""
    try:
        # This will raise a ZeroDivisionError
        result = 10 / 0
    except ZeroDivisionError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    finally:
        print("Error handling demonstration completed.")


def main():
    """Main function demonstrating the usage of classes and functions."""
    print("=== Python Code Demonstration ===\n")
    
    # Fibonacci demonstration
    print("Fibonacci Numbers:")
    for i in range(10):
        print(f"F({i}) = {fibonacci_iterative(i)}")
    print()
    
    # Calculator demonstration
    print("Calculator Demo:")
    calc = Calculator()
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    
    print("\nCalculation History:")
    for operation in calc.get_history():
        print(f"  {operation}")
    print()
    
    # Data processing demonstration
    print("Data Processing Demo:")
    numbers = [random.randint(1, 100) for _ in range(10)]
    print(f"Random numbers: {numbers}")
    
    even_numbers = DataProcessor.filter_even_numbers(numbers)
    print(f"Even numbers: {even_numbers}")
    
    stats = DataProcessor.calculate_statistics(numbers)
    print("Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    primes = DataProcessor.find_prime_numbers(30)
    print(f"Prime numbers up to 30: {primes}")
    print()
    
    # Error handling demonstration
    print("Error Handling Demo:")
    demonstrate_error_handling()


if __name__ == "__main__":
    main()