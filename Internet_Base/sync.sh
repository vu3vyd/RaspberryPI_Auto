#!/bin/bash
# =============================================================
#  sync.sh — Nightly GitHub sync + email status notification
#  Config : ~/.raspi_config  (shared with RaspIP.py)
#  Cron   : 50 23 * * *   (runs at 11:50 PM every night)
# =============================================================

export HOME=/home/pi          # ensures ~ expands correctly from cron

CONFIG="$HOME/.raspi_config"

# ── Load shared config ────────────────────────────────────────
if [ ! -f "$CONFIG" ]; then
    echo "ERROR: Config file not found: $CONFIG" >&2
    echo "  Create it: cp ~/RaspberryPI_Auto/raspi_config.template ~/.raspi_config" >&2
    exit 1
fi

# shellcheck source=/dev/null
source "$CONFIG"

# Validate required fields
MISSING=""
[ -z "$REPO" ]           && MISSING="$MISSING REPO"
[ -z "$SENDER_EMAIL" ]   && MISSING="$MISSING SENDER_EMAIL"
[ -z "$SMTP_PASSWORD" ]  && MISSING="$MISSING SMTP_PASSWORD"
[ -z "$RECIPIENT_EMAIL" ] && MISSING="$MISSING RECIPIENT_EMAIL"

if [ -n "$MISSING" ]; then
    echo "ERROR: Missing required fields in $CONFIG:$MISSING" >&2
    exit 1
fi

# ── Derived settings ──────────────────────────────────────────
BRANCH="${BRANCH:-main}"
DEVICE_NAME="${DEVICE_NAME:-$(hostname)}"
LOG="$REPO/sync.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# ── Email helper ──────────────────────────────────────────────
send_email() {
    local subject="$1"
    local body="$2"

    local TEMP_RC
    TEMP_RC=$(mktemp)
    chmod 600 "$TEMP_RC"

    cat > "$TEMP_RC" << MSMTPEOF
defaults
auth on
tls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account raspi
host smtp.gmail.com
port 587
from $SENDER_EMAIL
user $SENDER_EMAIL
password $SMTP_PASSWORD

account default : raspi
MSMTPEOF

    echo "$body" | msmtp -C "$TEMP_RC" "$RECIPIENT_EMAIL"
    local code=$?
    rm -f "$TEMP_RC"
    return $code
}

# ──────────────────────────────────────────────────────────────

echo "[$DATE] ── Sync started ──────────────────" >> "$LOG"

# 1. Ensure repo path exists
if [ ! -d "$REPO" ]; then
    BODY="[$DATE] FAILED: Repo directory not found at $REPO on $DEVICE_NAME."
    echo "$BODY" >> "$LOG"
    send_email "[Git Sync] FAILED — $DEVICE_NAME" "$BODY"
    exit 1
fi

cd "$REPO" || exit 1

# 2. Fetch remote without merging, then compare commits
FETCH_OUTPUT=$(git fetch origin "$BRANCH" 2>&1)
FETCH_CODE=$?
echo "$FETCH_OUTPUT" >> "$LOG"

if [ $FETCH_CODE -ne 0 ]; then
    BODY="Git fetch FAILED. Please investigate.

Device     : $DEVICE_NAME
Repo       : $REPO
Branch     : $BRANCH
Time       : $DATE
Exit code  : $FETCH_CODE

── Git output ─────────────────────────────
$FETCH_OUTPUT

── Log file ───────────────────────────────
$LOG"
    send_email "[Git Sync] FAILED — $DEVICE_NAME" "$BODY"
    echo "[$DATE] Fetch FAILED. Mail sent." >> "$LOG"
    echo "[$DATE] ── Sync ended ────────────────────" >> "$LOG"
    exit 1
fi

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "[$DATE] No changes detected (local == remote at $LOCAL). Skipping pull." >> "$LOG"
    echo "[$DATE] ── Sync ended ────────────────────" >> "$LOG"
    exit 0
fi

echo "[$DATE] Changes detected ($LOCAL -> $REMOTE). Pulling." >> "$LOG"

# 3. Pull and capture output
PULL_OUTPUT=$(git pull origin "$BRANCH" 2>&1)
EXIT_CODE=$?
echo "$PULL_OUTPUT" >> "$LOG"

# 4. Build email
if [ $EXIT_CODE -eq 0 ]; then
    STATUS="SUCCESS"
    BODY="Git sync completed successfully.

Device     : $DEVICE_NAME
Repo       : $REPO
Branch     : $BRANCH
Time       : $DATE

── Git output ─────────────────────────────
$PULL_OUTPUT

── Log file ───────────────────────────────
$LOG"
else
    STATUS="FAILED"
    BODY="Git sync FAILED. Please investigate.

Device     : $DEVICE_NAME
Repo       : $REPO
Branch     : $BRANCH
Time       : $DATE
Exit code  : $EXIT_CODE

── Git output ─────────────────────────────
$PULL_OUTPUT

── Log file ───────────────────────────────
$LOG"
fi

# 5. Send email
send_email "[Git Sync] $STATUS — $DEVICE_NAME" "$BODY"
MAIL_CODE=$?

# 6. Final log entry
echo "[$DATE] Sync $STATUS. Mail exit: $MAIL_CODE." >> "$LOG"
echo "[$DATE] ── Sync ended ────────────────────" >> "$LOG"
