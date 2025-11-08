#!/bin/bash

# ---------------------------------------------------------------------------
# Creative Commons CC BY 4.0 - David Romero - Diverso Lab
# ---------------------------------------------------------------------------
# This script is licensed under the Creative Commons Attribution 4.0 
# International License. You are free to share and adapt the material 
# as long as appropriate credit is given, a link to the license is provided, 
# and you indicate if changes were made.
#
# For more details, visit:
# https://creativecommons.org/licenses/by/4.0/
# ---------------------------------------------------------------------------

# Exit immediately on error, reference to unset var, and propagate errors in pipelines
set -euo pipefail

# Resolve repository root robustly no matter where this script is executed from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Candidate roots where the source code may live in Render/Docker
CANDIDATES=(
    "$SCRIPT_DIR/../.."           # repo root relative to this script
    "/app"                         # common WORKDIR in Docker images
    "/opt/render/project/src"      # Render native path
    "$(pwd)"                       # current working directory
)

REPO_ROOT=""
for d in "${CANDIDATES[@]}"; do
    if [ -f "$d/pyproject.toml" ]; then
        REPO_ROOT="$(cd "$d" && pwd)"
        break
    fi
done

if [ -z "$REPO_ROOT" ]; then
    echo "[render][ERROR] Could not locate repository root (pyproject.toml not found)."
    echo "[render] SCRIPT_DIR=$SCRIPT_DIR"
    echo "[render] CWD=$(pwd)"
    echo "[render] Contents of / and /app and /opt/render/project/src if present:"
    echo "--- ls -la / ---" && ls -la /
    if [ -d /app ]; then echo "--- ls -la /app ---" && ls -la /app; fi
    if [ -d /opt/render/project/src ]; then echo "--- ls -la /opt/render/project/src ---" && ls -la /opt/render/project/src; fi
    exit 1
fi

cd "$REPO_ROOT"
echo "[render] Using repository root: $REPO_ROOT"

# Install Rosemary (package at repo root where pyproject.toml lives)
python3 -m pip install --upgrade pip
# Install the project by absolute path to avoid CWD issues in Render
python3 -m pip install "$REPO_ROOT"

# Initialize migrations only if the migrations directory doesn't exist
if [ ! -d "migrations/versions" ]; then
    # Initialize the migration repository
    flask db init
    flask db migrate
fi

# Check if the database is empty
if [ $(mariadb -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';") -eq 0 ]; then
 
    echo "Empty database, migrating..."

    # Get the latest migration revision
    LATEST_REVISION=$(ls -1 migrations/versions/*.py | grep -v "__pycache__" | sort -r | head -n 1 | sed 's/.*\/\(.*\)\.py/\1/')

    echo "Latest revision: $LATEST_REVISION"

    # Run the migration process to apply all database schema changes
    flask db upgrade
    rosemary db:seed -y
    

else

    echo "Database already initialized, updating migrations..."

    # Get the current revision to avoid duplicate stamp
    CURRENT_REVISION=$(mariadb -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT version_num FROM alembic_version LIMIT 1;")
    
    if [ -z "$CURRENT_REVISION" ]; then
        # If no current revision, stamp with the latest revision
        flask db stamp head
    fi

    # Run the migration process to apply all database schema changes
    flask db upgrade
    rosemary db:seed -y
fi

# Start the application using Gunicorn, binding it to port 80
# Set the logging level to info and the timeout to 3600 seconds
exec gunicorn --bind 0.0.0.0:80 app:app --log-level info --timeout 3600