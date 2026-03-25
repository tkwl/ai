#!/bin/bash
# Vance Kessler Bridge Heartbeat
# Runs every 30 minutes via cron. Checks if the bridge systemd service
# is running, restarts it if not, and logs the result.
#
# Cron entry:
#   */30 * * * * /home/ubuntu/vance-kessler/scripts/heartbeat.sh >> /home/ubuntu/vance-kessler/logs/heartbeat.log 2>&1
#
# Optional: set HEARTBEAT_ALERT_CHAT_ID in .env to receive Telegram
# alerts when the bridge needs a restart.

set -euo pipefail

PROJECT_DIR="/home/ubuntu/vance-kessler"
SERVICE_NAME="vance-bridge.service"
LOG_DIR="$PROJECT_DIR/logs"
ENV_FILE="$PROJECT_DIR/.env"

mkdir -p "$LOG_DIR"

NOW=$(date -u '+%Y-%m-%d %H:%M:%S UTC')

# Load .env for optional Telegram alerting
TELEGRAM_BOT_TOKEN=""
HEARTBEAT_ALERT_CHAT_ID=""
if [ -f "$ENV_FILE" ]; then
    TELEGRAM_BOT_TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
    HEARTBEAT_ALERT_CHAT_ID=$(grep -E '^HEARTBEAT_ALERT_CHAT_ID=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
fi

send_telegram_alert() {
    local message="$1"
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$HEARTBEAT_ALERT_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${HEARTBEAT_ALERT_CHAT_ID}" \
            -d "text=${message}" \
            -d "parse_mode=Markdown" \
            --max-time 10 >/dev/null 2>&1 || true
    fi
}

# Check if the systemd service is active
if systemctl is-active --quiet "$SERVICE_NAME"; then
    # Service is running -- check process health
    PID=$(systemctl show "$SERVICE_NAME" --property=MainPID --value 2>/dev/null || echo "0")
    UPTIME=$(ps -o etime= -p "$PID" 2>/dev/null | xargs || echo "unknown")
    MEM=$(ps -o rss= -p "$PID" 2>/dev/null | awk '{printf "%.1f MB", $1/1024}' || echo "unknown")

    echo "[$NOW] OK: $SERVICE_NAME is running (PID=$PID, uptime=$UPTIME, mem=$MEM)"
    exit 0
fi

# Service is not running -- attempt restart
echo "[$NOW] DOWN: $SERVICE_NAME is not active. Attempting restart..."

# Try systemctl restart
if systemctl restart "$SERVICE_NAME" 2>&1; then
    # Wait briefly and verify
    sleep 5
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        PID=$(systemctl show "$SERVICE_NAME" --property=MainPID --value 2>/dev/null || echo "unknown")
        echo "[$NOW] RESTARTED: $SERVICE_NAME is back up (PID=$PID)"
        send_telegram_alert "*Vance Heartbeat*: Bridge was down and has been restarted successfully (PID=$PID)"
        exit 0
    else
        echo "[$NOW] FAILED: $SERVICE_NAME restart attempted but service is still not running"
        send_telegram_alert "*Vance Heartbeat ALERT*: Bridge is down and restart FAILED. Manual intervention needed."
        exit 1
    fi
else
    echo "[$NOW] FAILED: systemctl restart returned an error"
    send_telegram_alert "*Vance Heartbeat ALERT*: Bridge is down and systemctl restart failed. Manual intervention needed."
    exit 1
fi
