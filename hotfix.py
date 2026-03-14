
import re
from currencies_config import CURRENCY_SYMBOLS

def hotfix_currency_symbols():
    
    CURRENCY_SYMBOLS["FOK"] = "kr"
    CURRENCY_SYMBOLS["HRK"] = "kn"
    CURRENCY_SYMBOLS["UAH"] = "₴"
    CURRENCY_SYMBOLS["ZWG"] = "Z$"
    
    return "Symbols updated successfully!"

def run_hotfix():
    print("Running currency symbol hotfix...")
    result = hotfix_currency_symbols()
    print(result)

if __name__ == "__main__":
    run_hotfix()
