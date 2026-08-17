"""
Production-ish entry point.

Flask's built-in server is a development server: single-process, not meant for
real traffic, and it prints a warning to that effect.  Waitress is a pure-Python
WSGI server that works on Windows (gunicorn does not).

    python -m backend.wsgi
"""

from backend.app import app
from backend.src.utils import config


def main():
    from waitress import serve

    print(f"  [WSGI] Serving on http://{config.HOST}:{config.PORT}")
    serve(app, host=config.HOST, port=config.PORT, threads=8)


if __name__ == "__main__":
    main()
