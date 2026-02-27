
import sys
import os
import logging

# Configure local logging to capture output
logging.basicConfig(
    filename='bot_test_results.log',
    level=logging.INFO,
    format='%(message)s',
    filemode='w'
)

try:
    from simple_bot import simple_bot
    
    queries = [
        "Hello",
        "What is a CPU?",
        "Tell me about BIOS",
        "Who is RigMaster?",
        "What is the meaning of life?",
        "shipping",
        "How much is 5 + 5?",
        "What is a bottleneck?",
        "define photosynthesis"
    ]
    
    logging.info("--- STARTING BOT TEST ---")
    
    for q in queries:
        logging.info(f"\nQUERY: {q}")
        response = simple_bot.get_response(q)
        logging.info(f"RESPONSE: {response}")
        
    logging.info("\n--- TEST COMPLETE ---")

except Exception as e:
    logging.error(f"FATAL ERROR: {e}")
