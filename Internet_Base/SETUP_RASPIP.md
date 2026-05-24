# RaspIP Setup & Troubleshooting Guide

## Prerequisites Checklist

- [ ] Python 3.6+ installed (no extra packages needed)
- [ ] Gmail account with 2-Step Verification enabled
- [ ] Gmail App Password generated (NOT your regular Gmail password)
  - Go to: https://myaccount.google.com/apppasswords
- [ ] Device has internet access and can reach smtp.gmail.com:587

---

## Configuration

Both `RaspIP.py` and `sync.sh` read from a **single shared config file**: `~/.raspi_config`.
Set everything in one place — sender, password, recipient, device name, and email subject.

### Step 1: Create `~/.raspi_config`

```bash
cp ~/RaspberryPI_Auto/raspi_config.template ~/.raspi_config
nano ~/.raspi_config
chmod 600 ~/.raspi_config
```

Fill in your details:

```
REPO="/home/pi/RaspberryPI_Auto"
BRANCH="main"

SENDER_EMAIL="your_gmail@gmail.com"
SMTP_PASSWORD="your16charapppassword"
RECIPIENT_EMAIL="recipient@gmail.com"

DEVICE_NAME="MyRaspberryPi"
EMAIL_SUBJECT="Raspberry Pi IP address update"

CHECK_INTERVAL_SECONDS="3600"
STATE_FILE="/home/pi/.raspi_state.json"
```

> **Use an App Password**, not your regular Gmail password.
> Generate one at https://myaccount.google.com/apppasswords (2FA must be enabled first).

### Step 2: Run

```bash
python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py
```

---

## Running the Script

### Test Run

```bash
source ~/.raspi_env
python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py
```

Expected startup output:

```
[2026-05-24 14:30:45] INFO: Configuration validated successfully
[2026-05-24 14:30:45] INFO: Configuration File: /home/pi/.msmtprc
[2026-05-24 14:30:45] INFO: Device Name: MyPiDevice
[2026-05-24 14:30:45] INFO: State File: /home/pi/.raspi_state.json
[2026-05-24 14:30:45] INFO: Check Interval: 3600 seconds (60 minutes)
[2026-05-24 14:30:45] INFO: SMTP Server: smtp.gmail.com:587
[2026-05-24 14:30:45] INFO: From: your_email@gmail.com
[2026-05-24 14:30:45] INFO: To: recipient@gmail.com
[2026-05-24 14:30:45] INFO: Starting RaspIP monitor for device: MyPiDevice
```

### Run in Background (systemd)

Create `/etc/systemd/system/raspip.service`:

```ini
[Unit]
Description=RaspIP - Raspberry Pi IP Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RaspberryPI_Auto/Internet_Base
ExecStart=/usr/bin/python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

No `EnvironmentFile` needed — all config is read from `~/.raspi_config`.

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable raspip
sudo systemctl start raspip
sudo systemctl status raspip
```

View logs:

```bash
sudo journalctl -u raspip -f
```

### Run as Cron Job

```bash
crontab -e
# Add (starts at boot, logs to file):
@reboot sleep 30 && source /home/pi/.raspi_env && python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py >> /home/pi/raspip.log 2>&1 &
```

---

## Troubleshooting

### ❌ "Config file not found: ~/.raspi_config"

```bash
cp ~/RaspberryPI_Auto/raspi_config.template ~/.raspi_config
nano ~/.raspi_config
chmod 600 ~/.raspi_config
```

### ❌ "SENDER_EMAIL / SMTP_PASSWORD / RECIPIENT_EMAIL missing"

Open `~/.raspi_config` and confirm those keys are present and not left as placeholders:

```bash
grep -E "^(SENDER_EMAIL|SMTP_PASSWORD|RECIPIENT_EMAIL)" ~/.raspi_config
```

### ❌ "SMTP authentication failed"

1. Verify `SMTP_PASSWORD` in `~/.raspi_config` is a **Gmail App Password** (not your regular password)
   - Generate at: https://myaccount.google.com/apppasswords
   - Requires 2-Step Verification to be enabled first
2. Ensure there are no extra spaces around the password value

### ❌ "Network error while connecting to smtp.gmail.com:587"

```bash
ping 8.8.8.8
telnet smtp.gmail.com 587   # hangs or refused = port blocked
```

### ❓ "No email received after IP change"

1. Check your spam/junk folder
2. Confirm the script logged "Email sent successfully"
3. Verify the IP actually changed — the script only emails on changes:
   ```bash
   cat /home/pi/.raspi_state.json   # or your STATE_FILE path
   ```

---

## Important Notes

⚠️ **Single config for both tools:**
- `~/.raspi_config` is the only file you need to edit — it drives both RaspIP.py and sync.sh
- Never commit it to version control (it contains your password)
- Keep permissions at 600: `chmod 600 ~/.raspi_config`
- Use Gmail App Passwords, not your regular account password

✅ **Logging:**
- All activities are logged to stdout with timestamps
- Run manually first to confirm startup succeeds before deploying as a service
