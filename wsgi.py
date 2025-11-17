"""
WSGI entry point for production deployment.
Use with Gunicorn or other WSGI servers.

Example:
    gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 wsgi:app
"""

from server import app, socketio

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
