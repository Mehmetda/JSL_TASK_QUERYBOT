"""
App package initializer: best-effort .env loading for configuration.
This keeps runtime tolerant if python-dotenv is not installed.
"""
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # Silently continue if dotenv is unavailable
    pass


