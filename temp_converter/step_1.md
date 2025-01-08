# Step 1: Analyze and clarify the requirements for the temperature conversion function

## System Prompt
Here's a specialized system prompt for analyzing and clarifying the requirements for a temperature conversion function:

System Prompt:
You are an experienced software requirements analyst with expertise in temperature conversion systems and scientific computing. Your task is to analyze and clarify the requirements for a temperature conversion function. Approach this task with the following skills and perspectives:

1. Requirements elicitation: Ask probing questions to uncover unstated needs and assumptions about the temperature conversion function.

2. Technical knowledge: Utilize your understanding of different temperature scales (e.g., Celsius, Fahrenheit, Kelvin) and their conversion formulas.

3. Use case analysis: Consider various scenarios where this function might be used, from scientific applications to everyday temperature conversions.

4. Precision and accuracy: Address the level of precision required for the conversions and how to handle rounding errors.

5. Input validation: Consider how to handle invalid inputs or edge cases (e.g., absolute zero, extremely high temperatures).

6. Performance considerations: Think about the efficiency of the function, especially if it needs to handle large datasets or real-time conversions.

7. Internationalization: Consider how the function might need to adapt to different regional preferences for temperature scales.

8. Documentation: Prepare to clearly document the requirements, including function signatures, input/output specifications, and any constraints or assumptions.

9. Testing scenarios: Develop a list of test cases that would ensure the function meets all requirements.

10. Integration considerations: Think about how this function might integrate with larger systems or applications.

Use these skills to thoroughly analyze the given task, ask clarifying questions, and produce a detailed, well-structured set of requirements for the temperature conversion function. Your output should be clear, concise, and actionable for software developers who will implement this function.

## Result
Certainly! I'll analyze and clarify the requirements for the temperature conversion function. To do this effectively, I'll need to ask some clarifying questions and make some assumptions. Then, I'll provide a detailed set of requirements based on the information available.

Clarifying Questions:

1. Which temperature scales should the function support? (e.g., Celsius, Fahrenheit, Kelvin, Rankine)
2. Should the function handle bidirectional conversions between all supported scales, or only specific conversions?
3. What level of precision is required for the conversions? (e.g., whole numbers, one decimal place, four decimal places)
4. What is the expected input range for temperatures? Are there any limitations?
5. How should the function handle invalid inputs or out-of-range values?
6. Is there a specific programming language or environment this function needs to be compatible with?
7. Are there any performance requirements, such as handling a large number of conversions quickly?
8. Does the function need to support batch conversions or just single value conversions?
9. Are there any specific error handling or logging requirements?
10. Does the function need to be localizable for different regions?

Assumptions:
Since we don't have answers to these questions, I'll make some reasonable assumptions to proceed with the requirements analysis:

- The function will support Celsius, Fahrenheit, and Kelvin.
- Bidirectional conversions between all supported scales are required.
- Precision will be to two decimal places.
- The function should handle a wide range of temperatures, including extreme values.
- The function should be implemented in a language-agnostic manner.
- Single value conversions are the primary use case.
- Basic error handling is required.

Based on these assumptions, here are the detailed requirements for the temperature conversion function:

1. Functionality:
   1.1. The function shall convert temperatures between Celsius, Fahrenheit, and Kelvin.
   1.2. Conversions shall be bidirectional between all supported scales (C to F, C to K, F to C, F to K, K to C, K to F).
   1.3. The function shall accept a numeric input value and a string indicating the input scale.
   1.4. The function shall accept a string indicating the desired output scale.
   1.5. The function shall return the converted temperature as a numeric value.

2. Precision and Accuracy:
   2.1. All conversions shall be accurate to two decimal places.
   2.2. The function shall use appropriate rounding methods to ensure accuracy.

3. Input Validation:
   3.1. The function shall validate that the input temperature is a numeric value.
   3.2. The function shall validate that the input and output scales are valid (C, F, or K).
   3.3. The function shall handle temperatures below absolute zero (-273.15°C, -459.67°F, 0K) by returning an error message.

4. Error Handling:
   4.1. The function shall return appropriate error messages for invalid inputs.
   4.2. Error messages shall clearly indicate the nature of the error (e.g., "Invalid input scale", "Temperature below absolute zero").

5. Performance:
   5.1. The function shall perform conversions with minimal computational overhead.
   5.2. The function shall be optimized for single value conversions.

6. Usability:
   6.1. The function shall have a clear and intuitive interface.
   6.2. Input and output scales shall be case-insensitive (e.g., "C", "c", "Celsius" should all be valid).

7. Documentation:
   7.1. The function shall be accompanied by clear documentation explaining its usage, parameters, and return values.
   7.2. Documentation shall include examples of valid function calls and expected outputs.

8. Testing:
   8.1. A comprehensive set of unit tests shall be developed to verify the function's accuracy and error handling.
   8.2. Test cases shall include normal conversions, edge cases, and error scenarios.

9. Maintainability:
   9.1. The function's code shall be well-commented and follow best practices for readability and maintainability.
   9.2. The implementation shall be modular to allow for easy addition of new temperature scales in the future.

10. Integration:
    10.1. The function shall be designed to be easily integrated into larger systems or applications.
    10.2. The function shall not have any external dependencies
