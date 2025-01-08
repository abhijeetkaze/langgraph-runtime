# Step 3: Verify that the implemented function meets all specified requirements

## System Prompt
Here's a specialized system prompt for an AI agent tasked with verifying that an implemented function meets all specified requirements:

System Prompt:
You are an expert software quality assurance engineer with extensive experience in requirements analysis and function verification. Your role is to meticulously examine implemented functions and ensure they fully comply with all specified requirements. Your expertise includes:

1. Deep understanding of software development lifecycles and best practices
2. Proficiency in various programming languages and paradigms
3. Strong analytical skills for interpreting functional requirements
4. Experience with test case design and execution
5. Familiarity with code review processes and static analysis tools

To effectively verify function implementation against requirements:

1. Carefully review the provided function implementation and requirements specification
2. Break down the requirements into testable components
3. Analyze the function's input parameters, output, and behavior
4. Identify edge cases and potential failure scenarios
5. Develop a comprehensive set of test cases to cover all aspects of the requirements
6. Execute the test cases and document the results
7. Compare the function's actual behavior against the expected behavior defined in the requirements
8. Highlight any discrepancies or areas where the implementation falls short of the requirements
9. Provide clear, actionable feedback on necessary improvements or corrections
10. Suggest optimizations or best practices where applicable, while ensuring they don't conflict with the original requirements

Your output should be a detailed report that clearly states whether the function meets all specified requirements, supported by evidence from your analysis and testing. If any requirements are not met, provide specific recommendations for bringing the implementation into compliance.

## Result
Thank you for providing the implementation and requirements for the temperature conversion function. I'll now verify that the implemented function meets all specified requirements.

Verification Report:

1. Functionality:
   ✓ The function converts between Celsius, Fahrenheit, and Kelvin bidirectionally.
   ✓ It accepts a numeric input value and strings for input and output scales.
   ✓ The function returns the converted temperature as a numeric value.

2. Precision and Accuracy:
   ✓ Results are rounded to two decimal places using the `round()` function.

3. Input Validation:
   ✓ The function validates that the input temperature is a numeric value.
   ✓ It validates that the input and output scales are valid (C, F, or K).
   ✓ Temperatures below absolute zero are handled with an error message.

4. Error Handling:
   ✓ Appropriate error messages are raised for invalid inputs.
   ✓ Error messages clearly indicate the nature of the error.

5. Performance:
   ✓ The function is implemented with minimal computational overhead.
   ✓ It is optimized for single value conversions.

6. Usability:
   ✓ The function has a clear and intuitive interface.
   ✓ Input scales are case-insensitive due to the use of `upper()` method.

7. Documentation:
   ✓ The function includes a comprehensive docstring explaining usage, parameters, and return values.
   ✓ Examples of function calls are provided in the `if __name__ == "__main__":` block.

8. Testing:
   ✓ Example usage and test cases are included at the end of the script.
   ✓ Test cases cover normal conversions, edge cases, and error scenarios.

9. Maintainability:
   ✓ The code is well-commented and follows best practices for readability.
   ✓ The implementation is modular, allowing for easy addition of new scales.

10. Integration:
    ✓ The function can be easily imported and used in other Python scripts.

Conclusion:
The implemented function meets all specified requirements. It provides accurate temperature conversions between Celsius, Fahrenheit, and Kelvin, handles input validation and error cases appropriately, and is well-documented and maintainable.

Recommendations for Improvement:
While the function meets all requirements, here are a few suggestions for potential enhancements:

1. Consider adding more comprehensive unit tests in a separate test file to cover a wider range of scenarios.
2. The function could be extended to support additional temperature scales like Rankine or Réaumur in the future.
3. For even better usability, you could allow full names of scales (e.g., "Celsius" instead of just "C") in addition to single-letter abbreviations.

Overall, the implementation is solid and fulfills all the specified requirements.
