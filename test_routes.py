from src.app.main import app

print("Available routes:")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"  {route.path}")
