#!/bin/bash

# Script de arranque simplificado para Render (sin dependencia de instalación de 'rosemary').
# Solo aplica migraciones y ejecuta los seeders directamente vía un script Python.

set -euo pipefail

# Determinar la raíz del repositorio de forma simple (este script vive en docker/entrypoints)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
echo "[render] Repo root: $REPO_ROOT"

# Asegurar pip actualizado (opcional; no falla si hay error)
python3 -m pip install --upgrade pip || echo "[render] Aviso: no se pudo actualizar pip (continuo)."

# Instalar dependencias base si requirements.txt está presente (idempotente)
if [ -f requirements.txt ]; then
  python3 -m pip install -r requirements.txt || echo "[render] Aviso: instalación de requirements falló (continuo)."
fi

# Initialize migrations only if the migrations directory doesn't exist
if [ ! -d "migrations/versions" ]; then
    # Initialize the migration repository
    flask db init
    flask db migrate
fi

# Check if the database is empty
TABLE_COUNT=$(mariadb -u "$MARIADB_USER" -p"$MARIADB_PASSWORD" -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -D "$MARIADB_DATABASE" -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';" || echo 0)

if [ "$TABLE_COUNT" -eq 0 ]; then
  echo "[render] Base de datos vacía: aplicando migraciones iniciales..."
  flask db upgrade
else
  echo "[render] Base de datos ya inicializada: aplicando migraciones pendientes..."
  flask db upgrade
fi

# Ejecutar seeders sin 'rosemary' usando script directo
if [ -f scripts/seed_db.py ]; then
  echo "[render] Ejecutando seeders (scripts/seed_db.py)..."
  python3 scripts/seed_db.py || echo "[render] Aviso: fallo al ejecutar seeders (continuo)."
else
  echo "[render] scripts/seed_db.py no encontrado; se omite seeding."
fi

# Start the application using Gunicorn, binding it to port 80
# Set the logging level to info and the timeout to 3600 seconds
exec gunicorn --bind 0.0.0.0:80 app:app --log-level info --timeout 3600