# AI_CODING_INSTRUCTIONS.md

<!-- AI ASSISTANT: ALWAYS READ THIS FILE BEFORE MAKING CODE CHANGES -->
<!-- CHECKLIST:
- [ ] All functions have type hints
- [ ] Public functions have docstrings with Args/Returns/Raises
- [ ] Error handling includes logging with context
- [ ] Functions are under 20 lines
- [ ] Using specific exceptions, not generic
- [ ] Following KISS principle
-->

## Overview

This document provides guidelines for AI assistants working on this project. The primary goal is to maintain code quality through simplicity, clarity, and robustness.

## Core Principles

### 1. KISS (Keep It Simple, Stupid)

- **Prefer simple solutions over clever ones**
- Write code that a junior developer can understand
- Avoid premature optimization
- If you need to explain how something works, it's probably too complex
- Break complex problems into smaller, manageable pieces

### 2. Clean Code Standards

- **Naming Conventions**
  
  - Use descriptive, self-documenting names
  - Variables: `user_email` not `e`
  - Functions: `calculate_total_price()` not `calc()`
  - Classes: `UserAuthenticationService` not `AuthSvc`
  - Constants: `MAX_RETRY_ATTEMPTS` not `max_attempts`
- **Function Design**
  
  - Each function should do ONE thing well
  - Keep functions under 20 lines when possible
  - Limit parameters to 3 or fewer (use objects/dataclasses for more)
  - Functions should be pure when possible (no side effects)
  
  ```python
  # Good - Single responsibility, clear parameters
  def calculate_discount(price: float, discount_percentage: float) -> float:
      """Calculate the discounted price."""
      if not 0 <= discount_percentage <= 100:
          raise ValueError("Discount percentage must be between 0 and 100")
      return price * (1 - discount_percentage / 100)
  
  # Bad - Multiple responsibilities, unclear
  def process(p, d, u, s=True):
      if s:
          # save to database
          pass
      return p * (1 - d / 100) if u.is_premium else p
  ```
- **Code Structure**
  
  - Group related functionality together
  - Maintain consistent indentation and formatting
  - Remove commented-out code
  - Delete unused imports and variables

### 3. Error Handling

- **Never ignore errors silently**
- Implement proper error handling at every level:
  
  ```python
  # Good
  import logging
  from typing import Dict, Any
  
  logger = logging.getLogger(__name__)
  
  class UserDataError(Exception):
      """Custom exception for user data processing errors."""
      pass
  
  def process_user_data(user_id: int) -> Dict[str, Any]:
      try:
          data = fetch_user_data(user_id)
          return process_data(data)
      except ConnectionError as e:
          logger.error(f"Failed to fetch user data for {user_id}: {e}")
          raise UserDataError(f"Unable to process user {user_id}") from e
      except ValueError as e:
          logger.error(f"Invalid data format for user {user_id}: {e}")
          raise UserDataError(f"Data validation failed for user {user_id}") from e
  
  # Bad
  def process_user_data(user_id):
      try:
          data = fetch_user_data(user_id)
          return process_data(data)
      except:
          print("Error occurred")
          return None
  ```
- **Error Handling Rules**
  
  - Always log errors with context
  - Throw meaningful, specific errors
  - Handle errors at the appropriate level
  - Provide user-friendly error messages
  - Include error recovery strategies when possible
  - Validate inputs early and fail fast
  
  ```python
  # Good - Comprehensive error handling
  from typing import Optional
  import logging
  
  logger = logging.getLogger(__name__)
  
  class PaymentError(Exception):
      """Base exception for payment-related errors."""
      pass
  
  class InsufficientFundsError(PaymentError):
      """Raised when account has insufficient funds."""
      pass
  
  def process_payment(
      amount: float,
      account_id: str,
      retry_count: int = 3
  ) -> Optional[str]:
      """
      Process a payment transaction.
  
      Returns:
          Transaction ID if successful, None if all retries failed
      """
      if amount <= 0:
          raise ValueError(f"Invalid amount: {amount}")
  
      for attempt in range(retry_count):
          try:
              balance = get_account_balance(account_id)
              if balance < amount:
                  raise InsufficientFundsError(
                      f"Account {account_id} has insufficient funds. "
                      f"Required: {amount}, Available: {balance}"
                  )
  
              transaction_id = execute_transaction(account_id, amount)
              logger.info(f"Payment successful: {transaction_id}")
              return transaction_id
  
          except ConnectionError as e:
              logger.warning(
                  f"Connection failed on attempt {attempt + 1}/{retry_count}: {e}"
              )
              if attempt == retry_count - 1:
                  logger.error(f"All payment attempts failed for account {account_id}")
                  raise PaymentError("Payment service unavailable") from e
              time.sleep(2 ** attempt)  # Exponential backoff
  
          except InsufficientFundsError:
              # Don't retry for business logic errors
              raise
  ```

## Specific Guidelines

### Code Quality

1. **DRY (Don't Repeat Yourself)**
   
   - Extract common logic into reusable functions
   - Use constants for repeated values
   - Create utility functions for common operations
   
   ```python
   # Good - DRY principle
   from enum import Enum
   
   class OrderStatus(Enum):
       PENDING = "pending"
       PROCESSING = "processing"
       COMPLETED = "completed"
   
   def validate_email(email: str) -> bool:
       """Validate email format."""
       import re
       pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
       return bool(re.match(pattern, email))
   
   def send_order_notification(order_id: int, status: OrderStatus):
       email = get_customer_email(order_id)
       if validate_email(email):
           send_email(email, f"Order {order_id} is {status.value}")
   
   # Bad - Repeated logic
   def process_order(order_id):
       email = get_email(order_id)
       if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
           send_email(email, "Order is processing")
   
   def complete_order(order_id):
       email = get_email(order_id)
       if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
           send_email(email, "Order is completed")
   ```
2. **Type Hints and Documentation**
   
   - Always use type hints for function parameters and returns
   - Write docstrings for classes and public methods
   - Use type aliases for complex types
   
   ```python
   from typing import List, Dict, Optional, Union
   from datetime import datetime
   
   # Type alias for clarity
   UserId = int
   UserData = Dict[str, Union[str, int, datetime]]
   
   def get_active_users(
       since: datetime,
       limit: Optional[int] = None,
       include_admins: bool = True
   ) -> List[UserData]:
       """
       Retrieve active users since a given date.
   
       Args:
           since: Start date for user activity
           limit: Maximum number of users to return
           include_admins: Whether to include admin users
   
       Returns:
           List of user data dictionaries
   
       Raises:
           ValueError: If since date is in the future
       """
       if since > datetime.now():
           raise ValueError("Date cannot be in the future")
       # Implementation here
   ```
3. **Context Managers and Resource Handling**
   
   - Use context managers for resource management
   - Always close files, connections, and locks properly
   
   ```python
   # Good - Using context managers
   import sqlite3
   from contextlib import contextmanager
   
   @contextmanager
   def get_db_connection(db_path: str):
       """Context manager for database connections."""
       conn = sqlite3.connect(db_path)
       try:
           yield conn
       finally:
           conn.close()
   
   def get_user_count() -> int:
       with get_db_connection("app.db") as conn:
           cursor = conn.cursor()
           return cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
   
   # Bad - Manual resource management
   def get_user_count_bad():
       conn = sqlite3.connect("app.db")
       cursor = conn.cursor()
       count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
       conn.close()  # What if an exception occurs above?
       return count
   ```

### File Organization

- Keep files focused and single-purpose
- Use clear, consistent file naming
- Organize files by feature/domain, not by type
- Limit file size to ~200 lines (guideline, not rule)

### Operating System Compatibility

- Use `pathlib.Path` for file paths and avoid OS-specific commands

### Scripting

- Keep the in mind that this project should work easily on Linux, Mac, Windows
- All scripts should be in the scripts directory of the project

### Python-Specific Best Practices

1. **Use Python Idioms**
   
   ```python
   # Good - Pythonic
   # List comprehension for simple transformations
   squares = [x**2 for x in numbers if x > 0]
   
   # Use enumerate instead of range(len())
   for i, item in enumerate(items):
       print(f"{i}: {item}")
   
   # Use zip for parallel iteration
   for name, score in zip(names, scores):
       print(f"{name}: {score}")
   
   # Use any() and all()
   if any(user.is_admin for user in users):
       grant_admin_access()
   ```
2. **Prefer Built-in Functions and Libraries**
   
   ```python
   from collections import defaultdict, Counter
   from itertools import chain, groupby
   from functools import lru_cache
   
   # Use Counter for counting
   word_counts = Counter(words)
   
   # Use defaultdict to avoid KeyError
   user_groups = defaultdict(list)
   for user in users:
       user_groups[user.department].append(user)
   
   # Use lru_cache for expensive computations
   @lru_cache(maxsize=128)
   def expensive_calculation(n: int) -> int:
       # Complex calculation here
       return result
   ```

### Dependencies

- Minimize external dependencies
- Choose well-maintained, popular libraries
- Understand what each dependency does
- Keep dependencies up to date

## What NOT to Do

1. **Avoid Over-Engineering**
   
   - Don't create abstractions for single use cases
   - Don't implement features "just in case"
   - Don't use complex patterns when simple ones suffice
   
   ```python
   # Bad - Over-engineered for a simple task
   class AbstractDataProcessor(ABC):
       @abstractmethod
       def process(self, data): pass
   
   class CSVDataProcessorFactory:
       def create_processor(self, type): ...
   
   # Good - Simple and direct
   def process_csv_data(filepath: str) -> List[Dict]:
       with open(filepath, 'r') as f:
           return list(csv.DictReader(f))
   ```
2. **Avoid Code Smells**
   
   - Long parameter lists
   - Deeply nested conditionals
   - God objects/functions
   - Magic numbers/strings
   - Copy-paste programming
   - Mutable default arguments
   
   ```python
   # Bad - Multiple code smells
   def process_data(data, flag1=True, flag2=False, mode=1, 
                    options=[], threshold=0.75):  # Mutable default!
       if flag1:
           if mode == 1:  # Magic number
               if len(data) > 100:  # Magic number
                   if flag2:
                       # Deeply nested logic
                       pass
   
   # Good
   from dataclasses import dataclass
   from enum import Enum
   
   class ProcessingMode(Enum):
       STANDARD = 1
       ADVANCED = 2
   
   @dataclass
   class ProcessingOptions:
       enable_validation: bool = True
       enable_caching: bool = False
       mode: ProcessingMode = ProcessingMode.STANDARD
       threshold: float = 0.75
   
   MAX_BATCH_SIZE = 100
   
   def process_data(data: List, options: Optional[ProcessingOptions] = None):
       if options is None:
           options = ProcessingOptions()
   
       if len(data) > MAX_BATCH_SIZE:
           return process_in_batches(data, options)
   
       return process_single_batch(data, options)
   ```
3. **Avoid Poor Error Handling**
   
   - Empty except blocks
   - Catching generic exceptions
   - Logging and rethrowing without adding value
   - Swallowing errors
   - Using assertions for validation
   
   ```python
   # Bad examples
   try:
       result = risky_operation()
   except:  # Never use bare except
       pass
   
   try:
       value = int(user_input)
   except Exception as e:  # Too broad
       print(f"Error: {e}")
       raise  # No added value
   
   assert user_age > 0  # Don't use assert for validation
   
   # Good examples
   try:
       value = int(user_input)
   except ValueError as e:
       logger.error(f"Invalid input '{user_input}': {e}")
       raise ValidationError(f"Please enter a valid number") from e
   
   if user_age <= 0:
       raise ValueError(f"Age must be positive, got {user_age}")
   ```

## Communication

- Explain your reasoning for significant decisions
- Highlight potential issues or technical debt
- Suggest improvements when you see them
- Ask for clarification when requirements are ambiguous

## Example Checklist

Before submitting code, ensure:

- [ ] Code follows PEP 8 style guide
- [ ] All functions have type hints
- [ ] Docstrings are present for public functions/classes
- [ ] All functions have clear, single responsibilities
- [ ] Error handling is comprehensive
- [ ] No unnecessary complexity
- [ ] Code is self-documenting
- [ ] No print() statements or debug code
- [ ] All edge cases are considered
- [ ] Code is DRY
- [ ] No mutable default arguments
- [ ] Context managers used for resource handling
- [ ] Constants are named in UPPER_CASE
- [ ] f-strings used for string formatting (Python 3.6+)

## Project-Specific Instructions

[Project-Specific Instructions](./AI_PROJECT_SPECIFIC_INSTRUCTIONS.md)

---

Remember: Good code is written for humans to read, not just for computers to execute. When in doubt, choose clarity over cleverness.

