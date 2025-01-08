# Runtime Graph with LangGraph and Langchain

Research implementation of DAG (Directed Acyclic Graph) focusing on runtime graph generation and execution via LangGraph nodes. This is an exploratory project that intentionally avoids using LangChain tools and agent registry to enable flexible experimentation. A proper tool and custom agent registry will be implemented in future iterations (maybe). The current approach was chosen to explore core functionality without additional abstractions.

This experiemnt was inspired by [McCReuben's discussion](https://github.com/langchain-ai/langgraph/discussions/2219) on runtime graph generation in LangGraph.

## Overview

The system generates and executes DAG plans dynamically:

- Task complexity determines plan structure
- Supports both sequential and parallel execution
- Uses LangGraph nodes for better observability
- Implements validation for complex workflows

## Implementation

### Planning Stage

- Analyzes task complexity (1-2 steps for simple, 3-4 moderate, 5+ complex)
- Generates DAG based on requirements
- Determines agent selection and dependencies

### Execution Stage

- Converts plans to LangGraph StateGraph
- Manages parallel/sequential execution
- Handles state and dependencies
- Optional validation for complex tasks

## Install

```bash
uv venv
source .venv/bin/activate  # or `.venv/Scripts/activate` on Windows
uv pip install -e .
```

## Model Configuration

```bash
# Gets Claude by default
llm = create_llm()  
# Or for OpenAI:
llm = create_llm(LLMConfig(provider=ModelProvider.OPENAI))
```

## Give it a try

Simple Task:

```bash
runtime-graph -i "Create a Python function that converts temperatures between Celsius and Fahrenheit" -d -s -o ./temp_converter
```

Medium task:

```bash
runtime-graph -i "Make a todo list single-page app in ReactJS that can add, list, and delete tasks" -d -s -o ./todo_app
```

Complex task:

```bash
runtime-graph -i "Design a message queue system with retry logic and error handling" -d -s -o ./message_queue
```

## Command-Line Usage

The flags used:

- `-i` or `--input`: The task description
- `-d` or `--debug`: Enable debug logging
- `-s` or `--save-steps`: Save intermediate steps
- `-o` or `--output-dir`: Directory for step outputs

## Requirements

- Python 3.12 or newer
- OpenAI or Anthropic API key in `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable (or set in `~/.env` file)

## License

MIT

