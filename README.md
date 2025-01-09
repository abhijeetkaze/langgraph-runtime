# Runtime Graph with LangGraph and Langchain

**TL;DR** Research implementation of DAG (Directed Acyclic Graph) focusing on runtime graph generation and execution via LangGraph nodes. This exploratory project intentionally avoids using LangChain tools and agent registry to enable flexible experimentation. MCP server registry will be implemented in future iterations. I choose the current approach to explore core functionality without additional abstractions.

This experiment was inspired by [McCReuben's discussion](https://github.com/langchain-ai/langgraph/discussions/2219) on runtime graph generation in LangGraph.

## Overview

The system generates and executes DAG plans dynamically:

- Breaks down complex tasks intelligently
- Adapts plan execution strategy based on context and complexity
- Remembers context across multiple interactions
- Handles both simple requests and complex workflows

## Notable Concepts

### Dynamic Graph Generation

Instead of hardcoding execution flows, the system generates them on the fly. A simple request like "explain what photosynthesis is" might need just one step, while "design a fault-tolerant message queue system" could spawn a multi-step parallel process with requirement analysis, component design, and validation stages.

### Context Awareness

The system maintains context across interactions. Ask it to "design a fault-tolerant message queue" and then follow up with "elaborate on the retry mechanism" - it understands the connection and builds on the previous context.

### Adaptive Complexity

The system scales its response based on the task:

- Simple tasks → Direct execution
- Medium complexity → Basic planning and validation
- Complex tasks → Full requirement analysis and staged execution

## Workflow

### Planning Stage

- Analyzes task complexity (1-2 steps for simple, 3-4 moderate, 5+ complex)
- Generates DAG based on requirements
- Determines agent selection and dependencies

### Execution Stage

- Converts plans to LangGraph StateGraph
- Manages parallel/sequential execution
- Handles state and dependencies
- Optional validation for complex tasks

## Practical Scenarios

### Scenario 1: System Architecture Design

```python
# Initial design phase
result = await process_task(
    query= "Design a fault-tolerant message queue with retry mechanisms",
    thread_id= "mq-design"
)

# Detailed component exploration
await process_task(
    query= "Elaborate on the error handling and retry mechanisms",
    thread_id= "mq-design",
    previous_messages=result["messages"]
)
```

### Scenario 2: Interactive Learning

```bash
# Initial concept explanation
runtime-graph -i "Explain how photosynthesis works" --thread-id "bio-lesson"

# Deepen understanding with follow-up
runtime-graph -i "How do plants use the glucose they produce?" --thread-id "bio-lesson"
```

### Scenario 3: Multi-Stage Problem Solving

```bash
# Break down the problem
runtime-graph -i "Help me solve this calculus integration problem" --thread-id "math-help"

# Guide through solution steps
runtime-graph -i "Now show me how to verify the solution" --thread-id "math-help"
```

## Install

```bash
uv venv
source .venv/bin/activate  # or `.venv/Scripts/activate` on Windows
uv pip install -e .
```

Note: OpenAI or Anthropic API key in `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable (or set in `~/.env` file)

## Model Configuration

```bash
# Gets Claude by default
llm = create_llm()  
# Or for OpenAI:
llm = create_llm(LLMConfig(provider=ModelProvider.OPENAI))
```

## Command-Line Usage

The flags used:

- `-i` or `--input`: Task description to execute (required)
- `-d` or `--debug`: For debug logging
- `-s` or `--save-steps`: Save intermediate steps to files
- `-o` or `--output-dir`: Directory for step outputs [default: ./steps]
- `--thread-id`: Thread ID for conversation persistence [default: auto-generated UUID]
- `-h` or `--help`: Show help message
- `--version`: Show version information

```bash
# Basic Usage
runtime-graph -i "Your task description"

# With Debug Logging
runtime-graph -i "Your task" -d

# Save Intermediate Steps
runtime-graph -i "Your task" -s -o ./output_dir

# Using Thread ID for Conversation Continuity
runtime-graph -i "Initial question" --thread-id "conversation-1"
runtime-graph -i "Follow-up question" --thread-id "conversation-1"
```

Example Scenarios:

```bash
# Scenario 1: Educational Task
runtime-graph -i "Explain how photosynthesis works" \
 --thread-id "bio-lesson" \
    -s -o ./lesson_steps

# Follow-up
runtime-graph -i "How do plants use the glucose they produce?" \
 --thread-id "bio-lesson" \
    -s -o ./lesson_steps_followup

# Scenario 2: System Design Task
runtime-graph -i "Design a fault-tolerant message queue" \
 --thread-id "mq-design" \
    -s -o ./design_steps

# Follow-up
runtime-graph -i "Elaborate on the retry mechanism" \
 --thread-id "mq-design" \
    -s -o ./design_steps_followup
```

### Programmatic Usage

For more complex scenarios, you can use the Python API:

```python
from runtime_graph import create_llm, process_task, LLMConfig, ModelProvider

# Basic Usage
async def run_basic_task():
 result = await process_task(
        query= "Your task description",
        save_steps=True,
        output_dir="./steps"
    )

# Conversation Threading
async def run_conversation():
    # Initial query
 result = await process_task(
        query= "Design a system architecture",
        thread_id= "design-task"
    )
    
    # Follow-up with context
    await process_task(
        query= "Add error handling to the design",
        thread_id= "design-task",
        previous_messages=result.get("messages", [])
    )

# Custom LLM Configuration
async def run_with_custom_llm():
 llm_config = LLMConfig(
        provider=ModelProvider.OPENAI,
        temperature=0.7
    )
 llm = create_llm(llm_config)
    
 result = await process_task(
        query= "Your task",
        llm=llm
    )
```

Example Complex Workflow:

```python
async def run_research_workflow():
    # Initial research phase
 result = await process_task(
        query= "Analyze recent papers on transformer architectures",
        thread_id="research-123",
        save_steps=True,
        output_dir="./research_steps"
    )
    
    # Implementation phase
    await process_task(
        query= "Design an implementation based on the findings",
        thread_id="research-123",
        previous_messages=result.get("messages", []),
        save_steps=True,
        output_dir="./implementation_steps"
    )
    
    # Evaluation phase
    await process_task(
        query= "Create evaluation metrics for the implementation",
        thread_id="research-123",
        previous_messages=result.get("messages", []),
        save_steps=True,
        output_dir="./evaluation_steps"
    )
```

## Example Workflow

The repository includes an example workflow that demonstrates conversation threading and task history tracking.
You can find it in `example_workflow.py`:

```python
# Run the example workflow
python example_workflow.py
```

This example demonstrates:

- Interactive requirement gathering through clarifying questions
- Task decomposition and execution planning
- Task history tracking and visualization
- Context-aware follow-up handling
- Intermediate step preservation

Example output structure:

```code
=== Initial Task ===
Processing task: Design a fault-tolerant message queue
[Planning and execution details...]

=== Task History ===
[Context and state history...]

=== Follow-up Task ===
Processing task: Elaborate on the retry mechanism
[Additional planning and execution...]

=== Updated Task History ===
[Complete thread...]
```

The example saves intermediate steps to `./design_steps` and `./design_steps_followup` directories for inspection.

## TODO: Dynamic MCP Integration

It's definitely on the roadmap! Excited to bring this dynamic MCP integration to life and enhance the system's capabilities.

### Dynamic MCP Architecture

```python
class MCPRegistry:
    """Registry for available MCP servers and their capabilities"""
    async def get_servers_for_task(self, task_description: str) -> List[MCPServer]:
        """ Dynamically determine required MCP servers for a task"""
 ...

    async def get_servers_for_step(self, step: PlanStep) -> List[MCPServer]:
        """Determine MCP servers needed for a specific execution step"""
 ...

class DynamicMCPManager:
    """ Manages dynamic MCP server assignment during execution"  ""
    async def assign_servers(
        self, 
        step: PlanStep,
        registry: MCPRegistry
    ) -> MCPContext:
        """ Dynamically assign appropriate MCP servers to a step"""
 ...
```

### Conceptual Workflow

```python
# Define available MCP servers
registry = MCPRegistry([
    ArxivMCPServer(),
    GitHubMCPServer(),
    LocalFilesMCPServer(),
    DatabaseMCPServer(),
    # ... other available servers
])

# Meta-agent analyzes task and creates a plan
result = await process_task(
    query= "Research and implement a new attention mechanism",
    mcp_registry=registry,
    thread_id= "research-task"
)

# System might generate a plan like:
'''
1. Literature Review (Uses: ArxivMCP, SemanticScholarMCP)
2. Code Analysis (Uses: GitHubMCP, CodeSearchMCP)
3. Implementation (Uses: LocalFilesMCP, GitMCP)
4. Evaluation (Uses: WandBMCP, DatabaseMCP)
'''

# Each step gets its context dynamically
step_1_context = await mcp_registry.get_servers_for_step(
    step_id=1,  # Literature Review
    task_type=TaskType.RESEARCH
)
'''
Meta-agent assigns:
- ArxivMCP for paper access
- SemanticScholarMCP for citation analysis
- ZoteroMCP for note-taking
'''

step_2_context = await mcp_registry.get_servers_for_step(
    step_id=2,  # Code Analysis
    task_type=TaskType.CODE_ANALYSIS
)
'''
Meta-agent assigns:
- GitHubMCP for repository access
- CodeSearchMCP for similar implementations
- LocalFilesMCP for codebase context
'''
```

## Contributing

While this is primarily a research project, we're open to ideas and improvements. Feel free to:

- Share interesting use cases
- Propose tool integration patterns

## License

MIT
