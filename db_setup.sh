#!/bin/bash
set -e

# Define directories
BASE_DIR="/Users/vishvatejaguduguntla/Game_membership project/database"
DATA_DIR="$BASE_DIR/mysql_data"
TMP_DIR="$BASE_DIR/mysql_tmp"
SOCK_DIR="$BASE_DIR/mysql_socket"
SOCK_FILE="$SOCK_DIR/mysql.sock"
PORT=33066
PID_FILE="$BASE_DIR/mysql.pid"
LOG_FILE="$BASE_DIR/mysql.log"

echo "=== Setting up Local MySQL Database Instance ==="

# Clean up any existing directory if force reset is needed
# For now, let's just make sure they exist
mkdir -p "$DATA_DIR" "$TMP_DIR" "$SOCK_DIR"

# Check if already initialized. If not, initialize.
if [ ! -d "$DATA_DIR/mysql" ]; then
    echo "Initializing MySQL data directory..."
    mysqld --initialize-insecure \
        --datadir="$DATA_DIR" \
        --tmpdir="$TMP_DIR" \
        --user=$(whoami)
    echo "Initialization complete."
else
    echo "MySQL data directory already initialized."
fi

# Check if server is already running
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "MySQL is already running on PID $(cat "$PID_FILE")."
else
    echo "Starting MySQL on port $PORT..."
    mysqld --datadir="$DATA_DIR" \
        --tmpdir="$TMP_DIR" \
        --port=$PORT \
        --socket="$SOCK_FILE" \
        --mysqlx=OFF \
        --pid-file="$PID_FILE" \
        --log-error="$LOG_FILE" \
        --user=$(whoami) &
    
    # Wait for the socket file to be created and mysql to respond
    echo "Waiting for MySQL to start..."
    for i in {1..30}; do
        if [ -S "$SOCK_FILE" ]; then
            # Try to connect
            if mysql --socket="$SOCK_FILE" -u root -e "select 1" >/dev/null 2>&1; then
                echo "MySQL started successfully!"
                break
            fi
        fi
        sleep 1
    done

    if [ ! -S "$SOCK_FILE" ]; then
        echo "Error: MySQL failed to start after 30 seconds."
        echo "Check error log at $LOG_FILE:"
        cat "$LOG_FILE" | tail -n 20
        exit 1
    fi
fi

# Apply Schema and Seed Data
echo "Applying database schema..."
mysql --socket="$SOCK_FILE" -u root < "/Users/vishvatejaguduguntla/Game_membership project/schema.sql"

echo "Applying seed data..."
mysql --socket="$SOCK_FILE" -u root < "/Users/vishvatejaguduguntla/Game_membership project/seed.sql"

echo "=== MySQL Database Setup and Seeding Complete ==="
