#!/bin/bash
# =============================================================
#  sync.sh — Nightly GitHub sync + email status notification
#  Repo  : https://github.com/vu3vyd/RaspberryPI_Auto
#  Cron  : 50 23 * * *   (runs at 11:50 PM every night)
# =============================================================

export HOME=/home/pi          # ensures msmtp finds ~/.msmtprc from cron

# ── Configuration ─────────────────────────────────────────────
REPO="/home/pi/RaspberryPI_Auto"          # path where repo is cloned on Pi
BRANCH="main"
LOG="/home/pi/RaspberryPI_Auto/sync.log"  # log lives inside the repo
TO="your_email@gmail.com"                 # ← recipient address
FROM="your_gmail@gmail.com"               # ← Gmail used in .msmtprc
HOSTNAME_LABEL=$(hostname)
DATE=$(date '+%Y-%m-%d %H:%M:%S')
# ──────────────────────────────────────────────────────────────

echo "[$DATE] ── Sync started ──────────────────" >> "$LOG"

# 1. Ensure repo path exists
if [ ! -d "$REPO" ]; then
    BODY="[$DATE] FAILED: Repo directory not found at $REPO on $HOSTNAME_LABEL."
    echo "$BODY" >> "$LOG"
    echo "$BODY" | mail -s "[Git Sync] FAILED — $HOSTNAME_LABEL" -r "$FROM" "$TO"
    exit 1
fi

cd "$REPO" || exit 1

# 2. Run git pull and capture output + exit code
PULL_OUTPUT=$(git pull origin "$BRANCH" 2>&1)
EXIT_CODE=$?

echo "$PULL_OUTPUT" >> "$LOG"

# 3. Build email based on result
if [ $EXIT_CODE -eq 0 ]; then
    STATUS="SUCCESS"
    SUBJECT="[Git Sync] SUCCESS — $HOSTNAME_LABEL"
    BODY="Git sync completed successfully.

Host       : $HOSTNAME_LABEL
Repo       : $REPO
Branch     : $BRANCH
Time       : $DATE

── Git output ─────────────────────────────
$PULL_OUTPUT

── Log file ───────────────────────────────
$LOG"
else
    STATUS="FAILED"
    SUBJECT="[Git Sync] FAILED — $HOSTNAME_LABEL"
    BODY="Git sync FAILED. Please investigate.

Host       : $HOSTNAME_LABEL
Repo       : $REPO
Branch     : $BRANCH
Time       : $DATE
Exit code  : $EXIT_CODE

── Git output ─────────────────────────────
$PULL_OUTPUT

── Log file ───────────────────────────────
$LOG"
fi

# 4. Send email
echo "$BODY" | mail -s "$SUBJECT" -r "$FROM" "$TO"
MAIL_CODE=$?

# 5. Final log entry
echo "[$DATE] Sync $STATUS. Mail exit: $MAIL_CODE." >> "$LOG"
echo "[$DATE] ── Sync ended ────────────────────" >> "$LOG"
