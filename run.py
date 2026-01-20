from waitress import serve
from app import app  # your Flask instance

if __name__ == "__main__":
    # Use $PORT if running on Render, otherwise default to 8000 for local dev
    import os
    port = int(os.environ.get("PORT", 8000))
    serve(app, host="0.0.0.0", port=port)
