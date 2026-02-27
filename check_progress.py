try:
    with open('final_import_log.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Total lines in log: {len(lines)}")
        if lines:
            print("Last 5 lines:")
            for l in lines[-5:]:
                print(l.strip())
except Exception as e:
    print(f"Error: {e}")
