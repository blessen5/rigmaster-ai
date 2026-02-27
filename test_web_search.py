
import sys
import os
import logging

# Configure local logging
logging.basicConfig(
    filename='web_search_test.log',
    level=logging.INFO,
    format='%(message)s',
    filemode='w'
)

try:
    from simple_bot import simple_bot
    
    # This query should trigger the web search if not in Wiki/DDG-Instant
    queries = [
        "latest NVIDIA news 2024",
        "best budget cpu for gaming in 2025"
    ]
    
    logging.info("--- WEB SEARCH TEST ---")
    
    for q in queries:
        logging.info(f"\nQUERY: {q}")
        response = simple_bot.get_response(q)
        logging.info(f"RESPONSE:\n{response}")
        
    logging.info("\n--- TEST COMPLETE ---")

except Exception as e:
    logging.error(f"FATAL ERROR: {e}")
