from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> None:
    api_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(api_root))
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql://vistaflow:vistaflow@localhost:5432/vistaflow",
    )

    from app.main import app

    output_path = api_root / "openapi.json"
    output_path.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
