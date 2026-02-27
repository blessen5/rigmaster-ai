
import sys
import os

try:
    print("Importing simple_bot...")
    from simple_bot import simple_bot
    print("Import successful.")

    print("Testing get_response('hello')...")
    res = simple_bot.get_response("hello")
    print(f"Result: {res}")

    print("Testing get_response('what is python')...")
    res = simple_bot.get_response("what is python")
    print(f"Result: {res}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
