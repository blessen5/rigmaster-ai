import os
with open('debug_io.txt', 'w') as f:
    f.write('Python script started\n')
    try:
        import requests
        f.write('requests imported\n')
        import dotenv
        f.write('dotenv imported\n')
    except Exception as e:
        f.write(f'Import error: {str(e)}\n')
f.write('DONE')
