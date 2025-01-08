import asyncio
from typing import Dict, List, Optional, Any, TypedDict, Union, Annotated, NewType, Type
from functools import partial
import logging
import uuid
import re
import os
from pydantic import BaseModel, Field, conint
from enum import Enum
from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import colorlog

# Load environment variables
load_dotenv()

def setup_logger():
    """Configure colored logging with custom format.
    
    Sets up both the main application logger and adjusts third-party loggers
    to maintain consistent formatting and log levels while avoiding duplicate logs.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Custom formatter that only shows level for non-INFO logs
    class CustomFormatter(colorlog.ColoredFormatter):
        def format(self, record):
            # Remove level name for INFO logs
            if record.levelno == logging.INFO:
                self._fmt = '%(blue)s%(message)s%(reset)s'
            else:
                # Show level name for other log levels
                self._fmt = '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s'
            
            return super().format(record)

    # Create and configure handler
    handler = colorlog.StreamHandler()
    formatter = CustomFormatter(
        '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s',
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Remove existing handlers
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Configure third-party loggers
    for logger_name in ['httpx', 'urllib3']:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.handlers = []  # Remove existing handlers
        third_party_logger.propagate = True  # Let root logger handle it
        third_party_logger.setLevel(logging.WARNING)

    # Setup application logger
    app_logger = colorlog.getLogger(__name__)
    app_logger.handlers = []  # Remove existing handlers
    app_logger.propagate = False  # Prevent propagation to avoid double logging
    app_logger.addHandler(handler)
    app_logger.setLevel(logging.DEBUG)

    return app_logger
logger = setup_logger()

class ModelProvider(str, Enum):
    """Supported model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class LLMConfig(BaseModel):
    """Configuration for LLM usage"""
    provider: ModelProvider = Field(
        default=ModelProvider.ANTHROPIC,
        description="Model provider to use"
    )
    openai_model: str = Field(default="gpt-4o")
    claude_model: str = Field(default="claude-3-5-sonnet-20240620")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)

def create_llm(config: Optional[LLMConfig] = None) -> BaseChatModel:
    """Create a configured LLM instance
    
    This function creates an LLM that works exactly like ChatOpenAI,
    maintaining compatibility with .with_structured_output() and other
    LangChain features.
    
    Args:
        config: Optional LLM configuration
        
    Returns:
        BaseChatModel: Configured LLM instance
        
    Example:
        ```python
        # Use in existing code
        llm = create_llm()  # Gets Claude by default
        structured_llm = llm.with_structured_output(RequirementsQuestions)
        chain = questions_prompt | structured_llm
        
        # Or use OpenAI
        config = LLMConfig(provider=ModelProvider.OPENAI)
        llm = create_llm(config)
        ```
    """
    config = config or LLMConfig()
    
    try:
        if config.provider == ModelProvider.OPENAI:
            return ChatOpenAI(
                model=config.openai_model,
                temperature=config.temperature
            )
        return ChatAnthropic(
            model=config.claude_model,
            temperature=config.temperature
        )
            
    except Exception as e:
        logger.error(f"Error creating LLM with provider {config.provider}: {e}")
        # Fallback to Claude if OpenAI fails
        if config.provider == ModelProvider.OPENAI:
            logger.info("Falling back to Claude")
            return ChatAnthropic(
                model="claude-3-opus-20240229",
                temperature=config.temperature
            )
        raise
    
# Replace conint usage with a custom type
StepID = NewType('StepID', int)

class ActionType(str, Enum):
    """Available action types for plan steps"""
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    CREATE_PLAN = "create_implementation_plan"
    IMPLEMENT_SOLUTION = "implement_solution"
    VERIFY_REQUIREMENTS = "verify_requirements"
    GATHER_DATA = "gather_data"
    PROCESS_DATA = "process_data"
    VALIDATE_OUTPUT = "validate_output"
    ASK_CLARIFICATION = "ask_clarification"

    @property
    def description(self) -> str:
        """Get the description for this action type."""
        return {
            ActionType.ANALYZE_REQUIREMENTS: "Initial analysis of requirements and constraints",
            ActionType.CREATE_PLAN: "Create detailed implementation strategy based on analysis",
            ActionType.IMPLEMENT_SOLUTION: "Generate actual solution implementation",
            ActionType.VERIFY_REQUIREMENTS: "Verify solution meets all specified requirements",
            ActionType.GATHER_DATA: "Collect necessary information from various sources",
            ActionType.PROCESS_DATA: "Process and transform collected information",
            ActionType.VALIDATE_OUTPUT: "Validate generated output against requirements",
            ActionType.ASK_CLARIFICATION: "Request clarification on ambiguous requirements"
        }[self]

class PlanStep(BaseModel):
    """Individual step in the execution plan"""
    id: StepID = Field(
        description="The step number, an integer starting from 1 and incrementing by 1 for each step"
    )
    action: ActionType = Field(description="The action to be taken in the step")
    description: str = Field(description="What this step accomplishes")
    depends_on: List[StepID] = Field(
        default_factory=list,
        description="A list of step ids that must be completed before this step"
    )
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for this step, with dependent inputs being passed as $id"
    )

class Plan(BaseModel):
    """Complete execution plan"""
    steps: List[PlanStep] = Field(description="Ordered list of execution steps")
    description: str = Field(description="Overall plan description and strategy")

class StepResult(TypedDict, total=False):
    """Result of a step execution"""
    input: Dict[str, Any]
    result: Optional[str]
    system_prompt: Optional[str]

class PlannerState(BaseModel):
    """State for the planning stage with requirements gathering"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    context: Optional[Dict[str, Any]] = None
    requirements: Dict[str, Any] = Field(default_factory=dict)
    clarifying_questions: List[str] = Field(default_factory=list)
    question_responses: Dict[str, str] = Field(default_factory=dict)
    selected_plan: Optional[Plan] = None
    final_answer: Optional[str] = None
    current_stage: str = "generate_questions"

class GeneratedPlan(BaseModel):
    """Structured output for LLM plan generation"""
    steps: List[PlanStep] = Field(description="Steps to execute the plan")
    description: str = Field(description="High-level plan description")
    reasoning: str = Field(description="Explanation of plan structure and steps")
    available_actions: List[ActionType] = Field(
        default_factory=lambda: list(ActionType),
        description="List of available actions with descriptions"
    )
    
def dict_merge(dict1: Dict[str, StepResult], dict2: Dict[str, StepResult]) -> Dict[str, StepResult]:
    """Merge two dictionaries for concurrent state updates in the runtime graph.
    
    Used as a merge strategy for the RuntimeState's agent_results field to handle
    concurrent updates from parallel step executions. Preserves all results from
    both dictionaries.
    
    Args:
        dict1: First dictionary of step results
        dict2: Second dictionary of step results
        
    Returns:
        Dict[str, StepResult]: Combined dictionary containing all step results
    
    Example:
        >>> results1 = {"1": {"input": {}, "result": "first"}}
        >>> results2 = {"2": {"input": {}, "result": "second"}}
        >>> merged = dict_merge(results1, results2)
        >>> # merged = {"1": {...}, "2": {...}}
    """
    if not dict1:
        return dict2
    if not dict2:
        return dict1
        
    return {**dict1, **dict2}

class RuntimeState(TypedDict, total=False):
    """Runtime state for execution stage with concurrent execution support"""
    session_id: str
    plan: Plan
    step_data: Dict[str, PlanStep]
    agent_results: Annotated[Dict[str, StepResult], dict_merge]
    final_answer: Optional[str]


def substitute_variables(
    args: Dict[str, Any],
    depends_on: List[StepID],
    agent_results: Dict[str, StepResult]
) -> Dict[str, Any]:
    """Substitute variables in step arguments with results from previous steps.
    
    Replaces placeholder variables (e.g. $1, $2) in step arguments with actual results
    from previously executed steps. Handles nested dictionaries and lists.
    
    Args:
        args: Step arguments that may contain variable placeholders
        depends_on: List of step IDs this step depends on
        agent_results: Results from previously executed steps
        
    Returns:
        Dict[str, Any]: Updated arguments with variables replaced by actual values
        
    Example:
        >>> args = {"input": "Result from step 1: $1"}
        >>> depends_on = [1]
        >>> agent_results = {"1": {"result": "Hello"}}
        >>> result = substitute_variables(args, depends_on, agent_results)
        >>> # result = {"input": "Result from step 1: Hello"}
    """
    def substitute_value(value: Any) -> Any:
        """Recursively substitute variables in a value."""
        if isinstance(value, str):
            result = value
            pattern = r"\$(\d+)"
            matches = re.finditer(pattern, value)
            for match in matches:
                step_id = match.group(1)
                if step_id not in agent_results:
                    logger.warning(f"Referenced step {step_id} not found in results")
                    continue
                step_result = agent_results[step_id].get("result", "")
                result = result.replace(f"${step_id}", str(step_result))
            return result
        elif isinstance(value, dict):
            return {k: substitute_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [substitute_value(item) for item in value]
        return value
    
    try:
        # Verify all dependencies have results
        missing_deps = [str(dep) for dep in depends_on 
                       if str(dep) not in agent_results]
        if missing_deps:
            logger.warning(f"Missing results for dependent steps: {', '.join(missing_deps)}")
        
        return {key: substitute_value(value) for key, value in args.items()}
        
    except Exception as e:
        logger.error(f"Error during variable substitution: {e}")
        return args  # Return original args on error


async def ask_user_question(question: str, session_id: str) -> str:
    """Prompt the user with a question and get their response.
    
    Provides a simple CLI interface to ask the user a question and collect their response.
    Handles potential I/O errors and ensures proper string formatting.
    
    Args:
        question: Question to ask the user
        session_id: Unique identifier for the current session
        
    Returns:
        str: User's response, stripped of leading/trailing whitespace
        
    Raises:
        EOFError: If input stream is closed
        KeyboardInterrupt: If user interrupts input
    """
    try:
        # Format and display the question
        formatted_question = question.strip().rstrip('?') + '?'
        logger.info(f"\nQuestion: {formatted_question}")
        
        # Get user input with proper error handling
        response = input("Your response: ").strip()
        
        if not response:
            logger.warning("Received empty response from user")
            return ""
            
        logger.debug(f"Received response for session {session_id}: {response}")
        return response
        
    except EOFError:
        logger.error("Input stream closed unexpectedly")
        raise
        
    except KeyboardInterrupt:
        logger.info("\nUser interrupted input")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error during user input: {e}")
        raise

class RequirementsQuestions(BaseModel):
    """Structure for LLM-generated clarifying questions"""
    questions: List[str] = Field(
        description="List of clarifying questions",
        min_items=1,
        max_items=4
    )
    reasoning: str = Field(
        description="Explanation of why these questions are necessary"
    )

async def generate_questions(state: PlannerState) -> Dict[str, Any]:
    """Generate clarifying questions to gather task requirements.
    
    Uses GPT-4 to analyze the task and generate focused questions based on 
    task complexity and type. Scales the question count based on task scope.
    
    Args:
        state: Current planner state containing task query and context
        
    Returns:
        Dict[str, Any]: Updates to state including generated questions and next stage
    """
    questions_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert requirements analyst. Your task is to generate 
        focused questions to gather key requirements for the given task.
        
        Guidelines:
        - For simple tasks: 1-2 essential questions
        - For moderate tasks: 2-3 questions about requirements and constraints
        - For complex tasks: 3-4 detailed questions
        
        Focus on questions that will:
        1. Clarify core requirements
        2. Identify key constraints
        3. Surface any hidden assumptions
        
        Analyze the task first, then generate appropriate questions."""),
        ("user", """Task: {task}
        
        Context (if available): {context}
        
        Generate appropriate clarifying questions for this task.""")
    ])
    
    try:
        # Create LLM with structured output
        llm = create_llm() 
        structured_llm = llm.with_structured_output(RequirementsQuestions)
        
        # Create and execute chain
        chain = questions_prompt | structured_llm
        
        result = await chain.ainvoke({
            "task": state.query,
            "context": state.context if state.context else "No additional context provided"
        })
        
        logger.info(f"Generated {len(result.questions)} questions")
        logger.debug(f"Question generation reasoning: {result.reasoning}")
        
        # Filter out any malformed questions
        valid_questions = [q.strip() for q in result.questions if "?" in q]
        
        if not valid_questions:
            logger.warning("No valid questions generated, using fallback question")
            valid_questions = ["Can you provide more details about what you need?"]
        
        return {
            "clarifying_questions": valid_questions,
            "current_stage": "ask_questions"
        }
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        # Fallback to a basic question
        return {
            "clarifying_questions": ["Could you tell me more about your requirements?"],
            "current_stage": "ask_questions"
        }

async def ask_questions(state: PlannerState) -> Dict[str, Any]:
    """Ask clarifying questions to user and collect responses sequentially.
    
    Processes each unanswered question in sequence, collecting responses and
    updating state. Moves to plan creation once all questions are answered.
    
    Args:
        state: Current planner state containing questions and previous responses
        
    Returns:
        Dict[str, Any]: Updates to state including new responses or stage transition
    """
    try:
        # Find first unanswered question
        unanswered_questions = [
            q for q in state.clarifying_questions 
            if q not in state.question_responses
        ]
        
        if not unanswered_questions:
            logger.info("All questions answered, moving to plan creation")
            return {"current_stage": "create_plan"}
            
        # Get next question and collect response
        current_question = unanswered_questions[0]
        logger.debug(f"Asking question: {current_question}")
        
        response = await ask_user_question(current_question, state.session_id)
        
        # Update responses
        updates = {
            "question_responses": {
                **state.question_responses,
                current_question: response
            }
        }
        
        # Check if this was the last question
        if len(updates["question_responses"]) == len(state.clarifying_questions):
            logger.info("All questions answered, proceeding to plan creation")
            updates["current_stage"] = "create_plan"
        
        return updates
        
    except Exception as e:
        logger.error(f"Error during question asking: {e}")
        # If there's an error, move to plan creation with what we have
        return {"current_stage": "create_plan"}


async def generate_specialist_prompt(task_description: str) -> str:
    """Generate a specialized system prompt for a specific task.
    
    Focused system prompt that will help guide the AI agent
    in completing a specific type of task effectively. The prompt emphasizes the
    particular expertise and perspective needed.
    
    Args:
        task_description: Description of the task to generate a prompt for
        
    Returns:
        str: Generated system prompt for the task
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at crafting specialized system prompts for AI agents based on a given task description.
        Given a task description, generate a focused system prompt that includes the skills and tools needed to accomplish the task effectively.
        Focus on the specific expertise and perspective needed."""),
        ("user", """Task: {task}
        Generate a specialized system prompt that will help an AI complete this task effectively.
        Focus on the specific expertise and perspective needed.""")
    ])
    
    llm = create_llm() 
    chain = prompt | llm
    
    result = await chain.ainvoke({"task": task_description})
    return result.content

async def create_plan(state: PlannerState) -> Dict[str, Any]:
    """Create detailed execution plan based on gathered requirements.
    
    Analyzes requirements and generates a structured execution plan
    with appropriate steps and dependencies. Ensures proper error handling and
    plan validation.
    
    Args:
        state: Current planner state with requirements and context
        
    Returns:
        Dict[str, Any]: Updates to state including generated plan
        
    Raises:
        ValueError: If plan creation fails and no fallback can be generated
    """
    planner_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert system planner focused on creating efficient, appropriately-scaled solutions. Your goal is to create execution plans that match task complexity - no more, no less.

Before planning, analyze the task:

1. Complexity Assessment:
   - Is this a simple task (1-2 steps)?
   - Is this a moderate task (3-4 steps)?
   - Is this a complex task (5+ steps)?
   Justify your complexity rating.

2. Requirements Analysis:
   - What are the core requirements?
   - Are there any implicit requirements?
   - What could we safely eliminate?

3. Step Necessity:
   For each step you consider, ask:
   - Why is this step necessary?
   - What would break if we removed it?
   - Could this be combined with another step?

Available Actions (use only what's needed):
- analyze_requirements: Initial analysis of requirements
  When to use: Complex tasks with unclear requirements
  When to skip: Simple, clear requirements

- create_implementation_plan: Create detailed strategy
  When to use: Multi-step implementations needing coordination
  When to skip: Direct, single-step solutions

- implement_solution: Generate actual solution
  When to use: Always required
  Note: For simple tasks, this might be the only step needed

- verify_requirements: Verify solution meets requirements
  When to use: Critical systems, complex requirements
  When to skip: Simple, self-evident solutions

- gather_data: Collect necessary information
  When to use: Missing crucial information
  When to skip: All information is provided

- process_data: Process collected information
  When to use: Raw data needs transformation
  When to skip: Data is already in usable form

- validate_output: Validate generated output
  When to use: Complex output needing verification
  When to skip: Output is self-evidently correct

Guidelines for Plan Creation:

1. Start Minimal:
   - Begin with the minimum viable plan
   - Add steps only when necessity is clear
   - Prefer fewer steps unless complexity is justified

2. For Simple Tasks (1-2 steps):
   - Usually just implement_solution
   - Maybe one preparation step if needed
   - Avoid unnecessary validation steps

3. For Moderate Tasks (3-4 steps):
   - Focus on core workflow
   - Include basic validation
   - Keep dependencies straightforward

4. For Complex Tasks (5+ steps):
   - Include proper requirement analysis
   - Add necessary validation steps
   - Handle data processing explicitly

Technical Requirements:
1. Each step needs:
   - Unique ID (integer)
   - Clear action from available list
   - Explicit dependencies (using $id)
   - Specific, focused description

2. Dependencies:
   - Must reference existing steps
   - Use $id for variable references
   - Keep dependency chain clear

Before finalizing your plan, verify:
1. Could this be simpler?
2. Is each step truly necessary?
3. Are we overengineering?
4. Does complexity match requirements?

Example Simple Plan:
```python
SIMPLE_PLAN_TEMPLATE = {{{{
    "steps": [
        {{{{
            "id": 1,
            "action": "implement_solution",
            "description": "Generate direct solution",
            "args": {{"input": "user query"}}
        }}}}
    ]
}}}}
```

Example Complex Plan:
```python
COMPLEX_PLAN_TEMPLATE = {{{{
    "steps": [
        {{{{
            "id": 1,
            "action": "analyze_requirements",
            "description": "Analyze core requirements"
        }}}},
        {{{{
            "id": 2,
            "action": "gather_data",
            "description": "Collect necessary information",
            "depends_on": [1]
        }}}},
        {{{{
            "id": 3,
            "action": "implement_solution",
            "description": "Generate solution based on analysis",
            "depends_on": [1, 2],
            "args": {{{{
                "requirements": "$1",
                "data": "$2"
            }}}}
        }}}}
    ]
}}}}
```
        
        Create a focused, efficient plan without unnecessary steps."""),
        ("user", """Task: {task}

Requirements gathered:
{requirements}

Context:
{context}

Generate a structured execution plan.""")
    ])
    
    try:
        # Validate state has requirements
        if not state.question_responses:
            raise ValueError("No requirements gathered - cannot create plan")

        # Create LLM with structured output
        llm = create_llm() 
        structured_llm = llm.with_structured_output(GeneratedPlan)
        chain = planner_prompt | structured_llm
        
        # Format requirements for prompt
        requirements_str = "\n".join(
            f"Q: {q}\nA: {state.question_responses.get(q, 'No response')}"
            for q in state.clarifying_questions
        )
        
        # Generate plan
        result = await chain.ainvoke({
            "task": state.query,
            "requirements": requirements_str,
            "context": str(state.context) if state.context else "No additional context"
        })
        
        logger.info(f"Generated plan with {len(result.steps)} steps")
        logger.debug(f"Plan reasoning: {result.reasoning}")
        
        # Validate generated plan
        if not result.steps:
            raise ValueError("Generated plan contains no steps")
        
        # Convert to Plan model and validate
        plan = Plan(
            steps=result.steps,
            description=result.description
        )
        
        # Validate plan structure
        for step in plan.steps:
            if not step.action or not step.description:
                raise ValueError(f"Invalid step structure in generated plan: {step}")
                
            # Validate dependencies exist
            if step.depends_on:
                step_ids = {s.id for s in plan.steps}
                invalid_deps = [dep for dep in step.depends_on if dep not in step_ids]
                if invalid_deps:
                    raise ValueError(f"Step {step.id} has invalid dependencies: {invalid_deps}")
        
        return {
            "selected_plan": plan,
            "current_stage": "complete"
        }
        
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        try:
            # Create minimal fallback plan
            if not state.question_responses:
                raise ValueError("No requirements gathered - cannot create fallback plan")
                
            requirements_str = "\n".join(
                f"{q}: {state.question_responses.get(q, 'No response')}"
                for q in state.clarifying_questions
            )
            
            fallback_plan = Plan(
                steps=[
                    PlanStep(
                        id=StepID(1),
                        action=ActionType.ANALYZE_REQUIREMENTS,
                        description="Analyze gathered requirements",
                        args={"requirements": requirements_str}
                    ),
                    PlanStep(
                        id=StepID(2),
                        action=ActionType.IMPLEMENT_SOLUTION,
                        description="Generate solution based on analysis",
                        depends_on=[StepID(1)],
                        args={"analysis": "$1"}
                    )
                ],
                description="Fallback execution plan"
            )
            
            # Validate fallback plan
            if not fallback_plan.steps:
                raise ValueError("Failed to create valid fallback plan")
                
            logger.info("Created fallback plan due to original plan failure")
            return {
                "selected_plan": fallback_plan,
                "current_stage": "complete"
            }
            
        except Exception as fallback_error:
            logger.error(f"Failed to create fallback plan: {fallback_error}")
            raise ValueError(f"Could not create plan or fallback: {str(e)} -> {str(fallback_error)}")

from langchain_core.output_parsers import StrOutputParser

async def execute_step(
    state: RuntimeState,
    step_id: StepID,
    llm: Optional[ChatOpenAI] = None,
    save_steps: bool = False,
    output_dir: str = './steps'
) -> Dict[str, Any]:
    """Execute a single step in the execution plan.
    
    Handles step execution by:
    1. Generating specialized system prompt for the step
    2. Gathering context from dependent steps
    3. Substituting variables in arguments
    4. Executing the step with appropriate error handling
    
    Args:
        state: Current runtime state
        step_id: ID of step to execute
        llm: Optional LLM instance to use
        save_steps: Whether to save step results to files
        output_dir: Directory to save step files
        
    Returns:
        Dict[str, Any]: Updates to state including step results
    """
    try:
        step_key = str(step_id)
        step_info = state["step_data"][step_key]
        logger.info(f"Executing step #{step_key}: {step_info.description}")
        
        # Create or use provided LLM instance
        step_llm = llm or create_llm() 
        
        # Generate specialized system prompt
        system_prompt = await generate_specialist_prompt(step_info.description)
        logger.debug(f"Generated system prompt for step {step_id}")
        
        # Build context from dependencies
        context = []
        agent_results = state.get("agent_results", {})
        
        for dep in step_info.depends_on:
            if str(dep) in agent_results:
                result = agent_results[str(dep)].get("result")
                context.append(f"Previous step {dep}: {result}")
            else:
                logger.warning(f"Missing result for dependency {dep}")
                context.append(f"Previous step {dep}: Not found")
        
        # Substitute variables in arguments
        step_args = substitute_variables(
            step_info.args,
            step_info.depends_on,
            agent_results
        )
        
        # Create and execute prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", """Task: {task}

Previous steps:
{previous_steps}

Arguments:
{arguments}

Generate appropriate output for this task.""")
        ])
        
        chain = prompt | step_llm | StrOutputParser()
        result = await chain.ainvoke({
            "task": step_info.description,
            "previous_steps": "\n".join(context) if context else "No previous steps",
            "arguments": str(step_args)
        })
        
        # Access the result value correctly
        result_content = result.value['content'] if hasattr(result, 'value') else str(result)
        
        # Save step result if requested
        if save_steps:
            await save_step_result(
                step_id=step_id,
                description=step_info.description,
                system_prompt=system_prompt,
                result=result_content,
                output_dir=output_dir
            )
        
        # Prepare state updates
        updates = {
            "agent_results": {
                str(step_id): {
                    "input": step_args,
                    "result": result_content,
                    "system_prompt": system_prompt
                }
            }
        }
        
        # Set final answer if this is the last step
        if step_id == max(int(s_id) for s_id in state["step_data"].keys()):
            updates["final_answer"] = result_content
        
        return updates
        
    except Exception as e:
        logger.error(f"Error executing step {step_id}: {e}")
        raise

async def save_step_result(
    step_id: StepID,
    description: str,
    system_prompt: str,
    result: str,
    output_dir: str
) -> None:
    """Save step execution results to file.
    
    Args:
        step_id: Step identifier
        description: Step description
        system_prompt: Generated system prompt
        result: Step execution result
        output_dir: Directory to save results
    """
    try:
        step_file = os.path.join(output_dir, f"step_{step_id}.md")
        content = f"""# Step {step_id}: {description}

## System Prompt
{system_prompt}

## Result
{result}
"""
        os.makedirs(output_dir, exist_ok=True)
        with open(step_file, "w") as f:
            f.write(content)
            
    except Exception as e:
        logger.warning(f"Failed to save step {step_id} result: {e}")
        # Don't raise - this is a non-critical operation

def create_execution_graph(
    plan: Plan,
    save_steps: bool = False,
    output_dir: str = './steps'
) -> tuple[StateGraph, RuntimeState]:
    """Create execution graph from plan with proper dependencies.
    
    Builds a LangGraph execution graph based on the provided plan:
    1. Creates nodes for each step
    2. Adds edges based on dependencies
    3. Connects start/end nodes
    4. Prepares initial state
    
    Args:
        plan: Execution plan with steps and dependencies
        save_steps: Whether to save step results to files
        output_dir: Directory to save step files
        
    Returns:
        tuple: (Compiled graph, Initial runtime state)
    """
    # Initialize graph with RuntimeState
    graph = StateGraph(RuntimeState)

    # Create step data dictionary with string keys
    step_data = {str(step.id): step for step in plan.steps}
    logger.debug(f"Initialized step_data with keys: {list(step_data.keys())}")
    
    # Create LLM instance to be shared across steps
    llm = create_llm() 
    
    # Create step data dictionary
    step_data = {str(step.id): step for step in plan.steps}
    
    # Add nodes for each step
    for step in plan.steps:
        node_name = f"step_{step.id}"
        
        # Create node function with proper configuration
        node_fn = partial(
            execute_step,
            step_id=step.id,
            llm=llm,
            save_steps=save_steps,
            output_dir=output_dir
        )
        
        graph.add_node(node_name, node_fn)
        logger.debug(f"Added node: {node_name}")

    # Add edges based on dependencies
    for step in plan.steps:
        node_name = f"step_{step.id}"
        
        if step.depends_on:
            # Add edges from dependencies
            for dep_id in step.depends_on:
                dep_node_name = f"step_{dep_id}"
                graph.add_edge(dep_node_name, node_name)
                logger.debug(f"Added edge: {dep_node_name} -> {node_name}")
        else:
            # Connect to START if no dependencies
            graph.add_edge(START, node_name)
            logger.debug(f"Added edge: START -> {node_name}")

    # Find terminal steps (no other steps depend on them)
    all_dependencies = {dep for step in plan.steps for dep in step.depends_on}
    terminal_steps = [
        step for step in plan.steps 
        if step.id not in all_dependencies
    ]
    
    # Connect terminal steps to END
    for step in terminal_steps:
        graph.add_edge(f"step_{step.id}", END)
        logger.debug(f"Added edge: step_{step.id} -> END")

    # Prepare initial state ensuring string keys
    initial_state = RuntimeState(
        session_id=str(uuid.uuid4()),
        plan=plan,
        step_data=step_data,
        agent_results={}
    )

    return graph.compile(), initial_state

def create_planner_graph() -> StateGraph:
    """Create planning stage graph for requirements gathering.
    
    Builds a LangGraph for the planning phase that:
    1. Generates clarifying questions
    2. Asks questions sequentially
    3. Creates execution plan
    
    The graph uses conditional edges to control flow between stages.
    
    Returns:
        StateGraph: Compiled planning graph
    """
    # Initialize graph with PlannerState
    graph = StateGraph(PlannerState)
    
    # Add nodes
    graph.add_node("generate_questions", generate_questions)
    graph.add_node("ask_questions", ask_questions)
    graph.add_node("create_plan", create_plan)
    
    # Add basic edges first
    graph.add_edge(START, "generate_questions")
    
    def should_continue_questions(state: PlannerState) -> List[str]:
        """Determine next stage based on current state."""
        logger.debug(f"Current stage: {state.current_stage}, Questions remaining: {len(state.clarifying_questions)}")
        
        if state.current_stage == "generate_questions":
            return ["ask_questions"]
            
        if state.current_stage == "ask_questions":
            unanswered = [q for q in state.clarifying_questions 
                         if q not in state.question_responses]
            if unanswered:
                return ["ask_questions"]
            return ["create_plan"]
            
        return ["create_plan"]
    
    # Use conditional edges for state-based routing
    graph.add_conditional_edges(
        "generate_questions",
        should_continue_questions,
        {
            "ask_questions": "ask_questions",
            "create_plan": "create_plan"
        }
    )
    
    graph.add_conditional_edges(
        "ask_questions",
        should_continue_questions,
        {
            "ask_questions": "ask_questions",
            "create_plan": "create_plan"
        }
    )
    
    # Connect final node
    graph.add_edge("create_plan", END)
    
    return graph.compile()

async def process_task(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    save_steps: bool = False,
    output_dir: str = './steps'
) -> RuntimeState:
    """Process a task through planning and execution stages.
    
    Main entry point that:
    1. Runs planning graph to gather requirements and create plan
    2. Creates and runs execution graph based on plan
    3. Handles logging and error reporting
    
    Args:
        query: Task description to process
        context: Optional additional context
        save_steps: Whether to save step results to files
        output_dir: Directory to save step files
        
    Returns:
        RuntimeState: Final state after execution
        
    Raises:
        Exception: If any stage fails
    """
    try:
        # Planning Stage
        planner_graph = create_planner_graph()
        initial_planner_state = PlannerState(query=query, context=context)
        
        logger.info("Starting planning phase")
        planner_result = await planner_graph.ainvoke(initial_planner_state)
        
        if not planner_result.get("selected_plan"):
            raise ValueError("Planning phase completed but no plan was generated")
        
        plan = planner_result["selected_plan"]
        
        # Log generated plan
        logger.info(f"\nGenerated Plan: {plan.description}")
        for step in plan.steps:
            deps = ", ".join(map(str, step.depends_on)) if step.depends_on else "none"
            logger.info(f"Step {step.id}: {step.description} (Dependencies: {deps})")
        
        # Execution Stage
        logger.info("\nStarting execution phase")
        graph, initial_state = create_execution_graph(
            plan,
            save_steps=save_steps,
            output_dir=output_dir
        )
        
        final_state = await graph.ainvoke(initial_state)
        
        # Log execution results
        logger.info("\nExecution Results:")
        for step_id, result in final_state["agent_results"].items():
            step = final_state["step_data"][step_id]
            logger.info(f"\nStep {step_id} ({step.description}):")
            logger.info(f"Result: {result['result']}")
        
        if final_answer := final_state.get("final_answer"):
            logger.info(f"\nFinal Answer: {final_answer}")
        else:
            logger.warning("No final answer generated")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error during task processing: {str(e)}")
        raise

def cli() -> int:
    """Command-line interface for the runtime graph system.
    
    Handles command-line arguments and executes task processing.
    Provides feedback and error reporting to the user.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    import argparse
    
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Runtime Graph System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  runtime-graph --input "Create a Python script to process CSV files"
  runtime-graph --input "Analyze this dataset" --debug --save-steps
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Task description to execute'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--save-steps', '-s',
        action='store_true',
        help='Save intermediate steps to files'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./steps',
        help='Directory to save step files (default: ./steps)'
    )
    
    try:
        args = parser.parse_args()
        
        # Configure logging based on debug flag
        log_level = logging.DEBUG if args.debug else logging.INFO
        logging.getLogger().setLevel(log_level)
        
        # Create output directory if saving steps
        if args.save_steps:
            try:
                os.makedirs(args.output_dir, exist_ok=True)
                logger.debug(f"Created output directory: {args.output_dir}")
            except Exception as e:
                logger.error(f"Failed to create output directory {args.output_dir}: {e}")
                return 1
        
        # Execute task
        logger.info(f"Processing task: {args.input}")
        result = asyncio.run(process_task(
            query=args.input,
            save_steps=args.save_steps,
            output_dir=args.output_dir
        ))
        
        # Check execution success
        if result.get("final_answer"):
            logger.info("Task completed successfully")
            return 0
        else:
            logger.warning("Task completed but no final answer generated")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 1
        
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        if args.debug:
            logger.exception("Detailed error traceback:")
        return 1

if __name__ == "__main__":
    exit_code = cli()
    exit(exit_code)