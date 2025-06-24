# check_env.py
import sys
import os

try:
    import flask_babel
    print("--- Successfully imported flask_babel ---")
    print(f"Python Executable: {sys.executable}")

    # Comprueba la versión de forma segura para evitar el error
    version = getattr(flask_babel, '__version__', 'Not found (likely < 3.0)')
    print(f"Flask-Babel version: {version}")

    print(f"Flask-Babel location: {flask_babel.__file__}")
except ImportError as e:
    print(f"--- FAILED to import flask_babel ---")
    print(e)

print("\n--- sys.path ---")
for p in sys.path:
    print(p)

print("\n--- PYTHONPATH environment variable ---")
print(os.environ.get('PYTHONPATH'))
