from app.main import app

paths = [route.path for route in app.routes]
print(f"Total routes: {len(paths)}")
for p in paths:
    if "mentoring" in p:
        print(" -", p)
