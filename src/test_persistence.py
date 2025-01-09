import asyncio
import logging
from main import (
    process_task,
    create_planner_graph,
    setup_logger,
    StateGraph
)

logger = setup_logger()

async def get_task_history(planner_graph: StateGraph, thread_id: str):
    """Get the complete history of a task's execution."""
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get state history (most recent first)
    history = list(planner_graph.get_state_history(config))
    
    logger.info(f"\nTask History for thread {thread_id}:")
    for snapshot in history:
        logger.info(f"\nState Values: {snapshot.values}")
        # Handle both dictionary and object-like state values
        values = snapshot.values
        if isinstance(values, dict):
            if "messages" in values:
                logger.info("Messages:")
                for msg in values["messages"]:
                    logger.info(f"  {msg['role']}: {msg['content']}")
        else:
            if hasattr(values, 'query'):
                logger.info(f"Query: {values.query}")
            if hasattr(values, 'messages'):
                logger.info("Messages:")
                for msg in values.messages:
                    logger.info(f"  {msg['role']}: {msg['content']}")
            if hasattr(values, 'question_responses'):
                logger.info(f"Responses: {values.question_responses}")
        logger.info(f"Next Steps: {snapshot.next}")

async def main():
    # Configure logging
    logging.getLogger().setLevel(logging.INFO)
    
    try:
        # First execution
        logger.info("\n=== Initial Task ===")
        result = await process_task(
            query="What is the structure of the US Government?",
            thread_id="demo-2"
        )
        
        # Get task history
        logger.info("\n=== Task History ===")
        planner_graph = create_planner_graph()
        await get_task_history(planner_graph, "demo-2")
        
        # Continue the conversation with previous messages
        logger.info("\n=== Follow-up Task ===")
        previous_messages = result.get("messages", [])
        follow_up = await process_task(
            query="Can you explain more about its agencies?",
            thread_id="demo-2",  # Same thread ID for continuation
            previous_messages=previous_messages  # Pass previous conversation
        )
        
        # Get updated history
        logger.info("\n=== Updated Task History ===")
        await get_task_history(planner_graph, "demo-2")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())