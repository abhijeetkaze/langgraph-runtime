# Step 2: Implement the bi-directional temperature conversion function

## System Prompt
Here's a specialized system prompt for implementing a bi-directional temperature conversion function:

You are an expert software developer specializing in mathematical algorithms and unit conversions. Your task is to implement a bi-directional temperature conversion function. This function should be able to convert temperatures between Celsius and Fahrenheit in both directions.

Key skills and knowledge you possess:
1. Proficiency in algorithmic thinking
2. Understanding of temperature scales and their relationships
3. Experience in implementing mathematical formulas in code
4. Expertise in creating reusable and efficient functions

To complete this task effectively, consider the following:
1. The formula for converting Celsius to Fahrenheit: F = (C * 9/5) + 32
2. The formula for converting Fahrenheit to Celsius: C = (F - 32) * 5/9
3. Input validation to ensure the provided temperature is a valid number
4. Handling of edge cases, such as absolute zero or extremely high temperatures
5. Proper rounding or precision handling for the converted values
6. Clear and concise function naming and documentation

Your implementation should be flexible, allowing users to specify the input temperature scale and desired output scale. Ensure that your solution is efficient, accurate, and easy to use in various programming contexts.

## Result
Based on the requirements analysis, I'll now implement the bi-directional temperature conversion function. I'll use Python for this implementation, as it's a widely-used language that can easily be adapted to other languages if needed.

```python
import math

def convert_temperature(value, from_scale, to_scale):
    """
    Convert temperature between Celsius, Fahrenheit, and Kelvin.
    
    Args:
    value (float): The temperature value to convert.
    from_scale (str): The scale of the input temperature ('C', 'F', or 'K').
    to_scale (str): The desired output scale ('C', 'F', or 'K').
    
    Returns:
    float: The converted temperature, rounded to two decimal places.
    
    Raises:
    ValueError: If input is invalid or temperature is below absolute zero.
    """
    
    # Input validation
    if not isinstance(value, (int, float)):
        raise ValueError("Temperature value must be a number.")
    
    scales = {'C', 'F', 'K'}
    from_scale = from_scale.upper()
    to_scale = to_scale.upper()
    
    if from_scale not in scales or to_scale not in scales:
        raise ValueError("Invalid scale. Use 'C', 'F', or 'K'.")
    
    if from_scale == to_scale:
        return round(value, 2)
    
    # Convert to Celsius first
    if from_scale == 'F':
        celsius = (value - 32) * 5/9
    elif from_scale == 'K':
        celsius = value - 273.15
    else:
        celsius = value
    
    # Check for temperatures below absolute zero
    if celsius < -273.15:
        raise ValueError("Temperature is below absolute zero.")
    
    # Convert from Celsius to desired scale
    if to_scale == 'C':
        result = celsius
    elif to_scale == 'F':
        result = (celsius * 9/5) + 32
    else:  # to_scale == 'K'
        result = celsius + 273.15
    
    return round(result, 2)

# Example usage and testing
if __name__ == "__main__":
    print(convert_temperature(0, 'C', 'F'))  # Should print 32.0
    print(convert_temperature(100, 'C', 'K'))  # Should print 373.15
    print(convert_temperature(212, 'F', 'C'))  # Should print 100.0
    print(convert_temperature(273.15, 'K', 'C'))  # Should print 0.0
    
    # Error handling examples
    try:
        print(convert_temperature(-500, 'C', 'F'))
    except ValueError as e:
        print(f"Error: {e}")
    
    try:
        print(convert_temperature('invalid', 'C', 'F'))
    except ValueError as e:
        print(f"Error: {e}")
    
    try:
        print(convert_temperature(100, 'X', 'Y'))
    except ValueError as e:
        print(f"Error: {e}")
```

This implementation meets the requirements as follows:

1. Functionality: The function converts between Celsius, Fahrenheit, and Kelvin bidirectionally.
2. Precision and Accuracy: Results are rounded to two decimal places.
3. Input Validation: The function validates numeric input and correct scale specifications.
4. Error Handling: Appropriate error messages are raised for invalid inputs and temperatures below absolute zero.
5. Performance: The function is optimized for single value conversions with minimal overhead.
6. Usability: The interface is clear and intuitive, and scale inputs are case-insensitive.
7. Documentation: The function includes a docstring explaining usage, parameters, and return values.
8. Testing: Example usage and test cases are included at the end of the script.
9. Maintainability: The code is well-commented and modular.
10. Integration: The function can be easily imported and used in other Python scripts.

To use this function in a project, you can import it and call it with the appropriate parameters. For example:

```python
from temperature_converter
