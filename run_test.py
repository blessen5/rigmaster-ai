import traceback
import sys

sys.path.append('.')
try:
    import test_advanced_engine
    test_advanced_engine.run_tests()
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
