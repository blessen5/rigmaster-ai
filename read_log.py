try:
    with open('import_data_log.txt', 'rb') as f:
        data = f.read()
        print(f"Data length: {len(data)}")
        try:
            print(data.decode('utf-16'))
        except:
            try:
                print(data.decode('utf-8'))
            except:
                print("Could not decode")
except Exception as e:
    print(f"Error: {e}")
