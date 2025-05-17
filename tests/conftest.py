import os
import sys
import time
import multiprocessing
import pytest

# Add project root to path
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from run import app

# Helper to run app in a separate process
def run_app():
    app.run(port=5000, use_reloader=False)

@pytest.fixture(scope="session", autouse=True)
def flask_server():
    proc = multiprocessing.Process(target=run_app)
    proc.daemon = True
    proc.start()
    time.sleep(2)
    yield
    proc.terminate()
    proc.join(timeout=5)