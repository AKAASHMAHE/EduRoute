"""
Production WSGI entry point using Waitress (Windows-compatible).
Usage:
    python wsgi.py
    
Or with Gunicorn on Linux/macOS:
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    from waitress import serve
    host = app.config.get("HOST", "0.0.0.0")
    port = app.config.get("PORT", 5000)
    print(f"[Waitress] Serving {app.config.get('APPLICATION_NAME')} on http://{host}:{port}")
    serve(app, host=host, port=port, threads=4)
