# RaspIP Setup & Troubleshooting Guide

## Prerequisites Checklist

Before running `RaspIP.py`, ensure you have the following:

### 1. Python Requirements
- [ ] Python 3.6+ installed
- [ ] No additional Python packages needed (uses only stdlib)

### 2. Gmail Configuration
- [ ] Gmail account with 2-factor authentication enabled
- [ ] Gmail App Password generated (NOT your regular Gmail password)
  - Go to: https://myaccount.google.com/apppasswords
  - Select "Mail" and your device type
  - Copy the generated 16-character password

### 3. Network Requirements
- [ ] Device has internet connectivity
- [ ] Can reach smtp.gmail.com:587 (Gmail SMTP server)
- [ ] Port 587 is not blocked by firewall

---

## Configuration

RaspIP.py reads SMTP credentials from `~/.msmtprc` — the **same file used by
sync.sh**. If you have already configured `~/.msmtprc` for sync.sh, you only
need to set `RASPI_IP_EMAIL_TO`.

### Step 1: Create `~/.msmtprc` (SMTP credentials)

Copy the template and fill in your Gmail credentials:

```bash
cp ~/RaspberryPI_Auto/.msmtprc.template ~/.msmtprc
nano ~/.msmtprc
chmod 600 ~/.msmtprc   # msmtp requires restricted permissions
```

The file should look like this (replace placeholders):

```
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile        ~/.msmtp.log

account        gmail
host           smtp.gmail.com
port           587
from           your_email@gmail.com
user           your_email@gmail.com
password       your16charapppassword

account default : gmail
```

> **⚠️ Use an App Password**, not your regular Gmail password.
> Generate one at https://myaccount.google.com/apppasswords (requires 2FA enabled).

### Step 2: Set Required Environment Variable

```bash
export RASPI_IP_EMAIL_TO="recipient@gmail.com"   # Where to send notifications
```

### Step 3: (Optional) Set Additional Variables

```bash
export RASPI_IP_DEVICE_NAME="MyPiDevice"             # Default: system hostname
export RASPI_IP_EMAIL_SUBJECT="Pi IP update"         # Default: "Raspberry Pi IP address update"
export RASPI_IP_CHECK_INTERVAL_SECONDS="3600"        # Default: 3600 (1 hour)
export RASPI_IP_STATE_FILE="/home/pi/.raspi_state.json"  # Default: raspip_last_ips.json
```

### Create a Persistent Config File

For convenience, copy and edit the provided template:

```bash
cp ~/RaspberryPI_Auto/.raspi_env.template ~/.raspi_env
nano ~/.raspi_env
chmod 600 ~/.raspi_env
```

Load it before running:

```bash
source ~/.raspi_env
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
EnvironmentFile=/home/pi/.raspi_env
ExecStart=/usr/bin/python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

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

### ❌ "Cannot read .msmtprc" / ".msmtprc file not found"

```bash
# Check the file exists
ls -la ~/.msmtprc

# If missing, create from template
cp ~/RaspberryPI_Auto/.msmtprc.template ~/.msmtprc
nano ~/.msmtprc
chmod 600 ~/.msmtprc
```

### ❌ "No account section found in .msmtprc"

The file exists but has no `account` block. Ensure your `~/.msmtprc` contains:

```
account        gmail
host           smtp.gmail.com
...
```

### ❌ ".msmtprc missing 'user' / 'password' / 'from' field"

Open `~/.msmtprc` and verify the `account gmail` block has all three fields filled in
(not left as placeholder text):

```bash
cat ~/.msmtprc
```

### ❌ "RASPI_IP_EMAIL_TO environment variable not set"

```bash
export RASPI_IP_EMAIL_TO="recipient@gmail.com"
# Or add it to ~/.raspi_env and run: source ~/.raspi_env
```

### ❌ "SMTP authentication failed"

1. Verify you are using a **Gmail App Password** (16 chars), not your regular password
   - Generate at: https://myaccount.google.com/apppasswords
   - Requires 2-Step Verification to be enabled first
2. Ensure the password in `~/.msmtprc` has no trailing spaces
3. Verify 2FA is enabled: https://myaccount.google.com/security

### ❌ "Network error while connecting to smtp.gmail.com:587"

```bash
# Test connectivity
ping 8.8.8.8
telnet smtp.gmail.com 587
# If telnet hangs or is refused, port 587 is blocked by your network
```

### ❓ "No email received after IP change"

1. Check your spam/junk folder
2. Confirm the script logged "Email sent successfully"
3. Check whether the IP actually changed (script only emails on changes):
   ```bash
   cat raspip_last_ips.json   # or your RASPI_IP_STATE_FILE path
   ```

---

## Important Notes

⚠️ **Shared configuration with sync.sh:**
- Both RaspIP.py and sync.sh read SMTP credentials from `~/.msmtprc`
- One file configures email for both tools
- RaspIP.py additionally requires `RASPI_IP_EMAIL_TO` (recipient address)
- sync.sh has `TO` and `FROM` hardcoded inside the script itself

⚠️ **Security:**
- Never commit `~/.msmtprc` or `~/.raspi_env` to version control
- Keep permissions at 600: `chmod 600 ~/.msmtprc ~/.raspi_env`
- Use Gmail App Passwords, not your account password

✅ **Logging:**
- All activities are logged to stdout with timestamps
- Run manually to see detailed output before setting up as a service
