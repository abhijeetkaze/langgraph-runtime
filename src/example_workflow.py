import asyncio
import logging
from main import (
    process_task,
    get_task_history,
    create_planner_graph,
    setup_logger,
)

logger = setup_logger()

async def main():
    # Configure logging
    logging.getLogger().setLevel(logging.INFO)
    
    try:
        # First execution
        logger.info("\n=== Initial Task ===")
        result = await process_task(
            query="Design a fault-tolerant message queue",
            thread_id="mq-desig",
            save_steps=True,
            output_dir="./design_steps"
        )
        
        # Get task history
        logger.info("\n=== Task History ===")
        planner_graph = create_planner_graph()
        await get_task_history(planner_graph, "mq-desig")
        
        # Continue the conversation
        logger.info("\n=== Follow-up Task ===")
        previous_messages = result.get("messages", [])
        result = await process_task( 
            query="Elaborate on the retry mechanism",
            thread_id="mq-desig",
            previous_messages=previous_messages,
            save_steps=True,
            output_dir="./design_steps_followup"
        )
        
        # Get updated history
        logger.info("\n=== Updated Task History ===")
        await get_task_history(planner_graph, "mq-desig")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())