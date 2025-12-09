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

# Exit immediately if a command exits with a non-zero status
set -e

# Sync uploads folder with Git repository
if [ -n "$UPLOADS_GIT_REPO_URL" ]; then
    echo "Synchronizing uploads folder..."
    sh /app/scripts/sync_uploads.sh
else
    echo "UPLOADS_GIT_REPO_URL not set, skipping uploads sync"
    mkdir -p "${WORKING_DIR}uploads"
fi

# Initialize migrations only if the migrations directory doesn't exist
if [ ! -d "migrations/versions" ]; then
    # Initialize the migration repository
    flask db init
    flask db migrate
fi

# Check if the database is empty
if [ $(mariadb --skip-ssl -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';") -eq 0 ]; then

    echo "Empty database, migrating..."

    # Get the latest migration revision
    LATEST_REVISION=$(ls -1 migrations/versions/*.py | grep -v "__pycache__" | sort -r | head -n 1 | sed 's/.*\/\(.*\)\.py/\1/')

    echo "Latest revision: $LATEST_REVISION"

    # Run the migration process to apply all database schema changes
    flask db upgrade

else

    echo "Database already initialized, updating migrations..."

    # Get the current revision to avoid duplicate stamp
    CURRENT_REVISION=$(mariadb --skip-ssl -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT version_num FROM alembic_version LIMIT 1;")

    if [ -z "$CURRENT_REVISION" ]; then
        # If no current revision, stamp with the latest revision
        flask db stamp head
    fi

    # Run the migration process to apply all database schema changes
    flask db upgrade
fi

# Seed the database if it's empty (no users exist) and seeding is enabled (variable only for staging, not production)
USER_COUNT=$(mariadb --skip-ssl -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT COUNT(*) FROM user;" 2>/dev/null || echo "0")

if [ "$USER_COUNT" -eq 0 ] && [ "$ENABLE_SEEDER" = "true" ]; then
    echo "No users found and ENABLE_SEEDER=true, seeding database..."
    rosemary db:seed
    echo "Database seeded successfully!"
elif [ "$USER_COUNT" -eq 0 ]; then
    echo "No users found, but ENABLE_SEEDER is not enabled. Skipping seed."
else
    echo "Database already has data, skipping seed."
fi

# Start the application using Gunicorn, binding it to port 80
# Set the logging level to info and the timeout to 3600 seconds
exec gunicorn --bind 0.0.0.0:80 app:app --log-level info --timeout 3600