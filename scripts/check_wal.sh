#!/usr/bin/env bash
DB=${1:-$(python -c "from config import DB_PATH; print(DB_PATH)" 2>/dev/null || echo "planos_luan.db")}
if [ ! -f "$DB" ]; then
  echo "DB not found: $DB"
  exit 1
fi
python - <<PY
import sqlite3
c=sqlite3.connect("$DB")
print("journal_mode:", c.execute("PRAGMA journal_mode;").fetchone())
print("synchronous:", c.execute("PRAGMA synchronous;").fetchone())
c.close()
PY
