#!/usr/bin/env python3
"""
Example Python file for MCP indexing demo.

This file demonstrates various Python concepts that can be searched
through the MCP local indexing server.
"""

def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using recursion.
    
    Args:
        n: The position in the Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Fibonacci sequence not defined for negative numbers")
    elif n <= 1:
        return n
    else:
        return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


class DataProcessor:
    """
    A simple data processor class for demonstration.
    
    Handles various data processing operations including
    filtering, transformation, and validation.
    """
    
    def __init__(self, name: str) -> None:
        """Initialize the processor with a name."""
        self.name = name
        self.processed_count = 0
    
    def process_data(self, data: list) -> list:
        """
        Process a list of data items.
        
        Args:
            data: List of items to process
            
        Returns:
            Processed data list
        """
        result = []
        for item in data:
            if self.validate_item(item):
                processed_item = self.transform_item(item)
                result.append(processed_item)
                self.processed_count += 1
        
        return result
    
    def validate_item(self, item) -> bool:
        """Validate an individual item."""
        return item is not None and str(item).strip() != ""
    
    def transform_item(self, item) -> str:
        """Transform an item to string format."""
        return f"processed_{str(item).lower()}"


# Example usage
if __name__ == "__main__":
    # Fibonacci example
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {calculate_fibonacci(i)}")
    
    # Data processor example
    processor = DataProcessor("demo_processor")
    sample_data = ["Apple", "Banana", "", "Cherry", None, "Date"]
    result = processor.process_data(sample_data)
    
    print(f"\nProcessed {processor.processed_count} items:")
    for item in result:
        print(f"  - {item}")