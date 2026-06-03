#!/bin/bash
BASE_DIR="/Users/vishvatejaguduguntla/Game_membership project/database"
PID_FILE="$BASE_DIR/mysql.pid"
SOCK_FILE="$BASE_DIR/mysql_socket/mysql.sock"

echo "=== Stopping Local MySQL Database Instance ==="

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Stopping MySQL process $PID..."
    kill "$PID"
    
    # Wait for it to stop
    for i in {1..15}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "MySQL stopped."
            rm -f "$PID_FILE"
            exit 0
        fi
        sleep 1
    done
    echo "MySQL did not stop within 15 seconds. Forcing shutdown..."
    kill -9 "$PID"
    rm -f "$PID_FILE"
else
    # Try using mysqladmin via socket if pid file not found
    if [ -S "$SOCK_FILE" ]; then
        echo "Stopping MySQL via socket..."
        mysqladmin --socket="$SOCK_FILE" -u root shutdown
    else
        echo "No PID file found and socket not active. MySQL is likely not running."
    fi
fi
