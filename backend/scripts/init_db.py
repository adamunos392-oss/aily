"""create_all + seed。用法：cd backend && PYTHONPATH=.. python3.12 scripts/init_db.py"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from pycore.core import get_logger  # noqa: E402

from src.db.session import DATABASE_FILE, init_db  # noqa: E402


async def main() -> None:
    await init_db()
    get_logger().info("init_db 脚本完成", db_path=str(DATABASE_FILE))


if __name__ == "__main__":
    asyncio.run(main())
