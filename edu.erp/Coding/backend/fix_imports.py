# fix_imports.py
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent / "app" / "api" / "v1" / "cudo_module"

# Define regex patterns for relative imports and their replacements
patterns = [
    (r"from \.+core\.database import get_db", "from app.core.database import get_db"),
    (r"from \.+core\.database import Base", "from app.core.database import Base"),
    (r"from \.+utils\.auth_helper import get_current_user", "from app.utils.auth_helper import get_current_user"),
    (r"from \.+utils\.http_return_helper import returnSuccess, returnException", "from app.utils.http_return_helper import returnSuccess, returnException"),
]

for py_path in BASE_DIR.rglob("*.py"):
    content = py_path.read_text(encoding="utf-8")
    new_content = content
    for pat, repl in patterns:
        new_content = re.sub(pat, repl, new_content)
    if new_content != content:
        py_path.write_text(new_content, encoding="utf-8")
        print(f"Updated imports in {py_path}")
