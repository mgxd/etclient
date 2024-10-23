import os


def _check_server_available() -> bool:
    """Checks if the server is locally available."""
    import requests

    try:
        res = requests.get('http://localhost:8080/', timeout=1)
    except Exception:
        print("Could not connect to server")
        return False
    if res.headers.get('X-Backend-Server') != 'migas':
        print(f"Migas server is not properly configured: {res.headers}")
        return False
    return True

run_server_tests = _check_server_available() and os.getenv('MIGAS_FRESH_DB')
