import uvicorn
import sys
import os

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from main import app
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='debug')
except Exception as e:
    print('Exception while running uvicorn:')
    import traceback
    traceback.print_exc()
    sys.exit(1)
