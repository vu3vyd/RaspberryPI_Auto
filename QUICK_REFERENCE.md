# Quick Reference Card

## Setup

```bash
cp raspi_config.template ~/.raspi_config
nano ~/.raspi_config      # fill in sender, password, recipient, device name, subject
chmod 600 ~/.raspi_config
```

One file — used by both RaspIP.py and sync.sh.

---

## Running Tools

### RaspIP.py (IP Monitoring)
```bash
source ~/.raspi_env
python3 Internet_Base/RaspIP.py
```

### sync.sh (Git Sync)
```bash
bash sync.sh
```

### GPS Testing
```bash
python3 Hardware_Base/GPSTest.py
```

---

## Configuration Files

| File | Location | Contains |
|------|----------|----------|
| Shared config | ~/.raspi_config | All settings for both tools |
| State file | as set in STATE_FILE | Last known IPs |
| Sync log | ~/RaspberryPI_Auto/sync.log | Sync history |

---

## Common Troubleshooting

| Problem | Solution |
|---------|----------|
| Config file not found | `cp raspi_config.template ~/.raspi_config && nano ~/.raspi_config` |
| Permission denied | `chmod 600 ~/.raspi_config` |
| Auth failed | Check `SMTP_PASSWORD` is a Gmail App Password |
| No email sent | Check `SENDER_EMAIL`, `SMTP_PASSWORD`, `RECIPIENT_EMAIL` in config |
| Missing field error | Open `~/.raspi_config` and fill in the missing value |

---

## Cron Jobs

### RaspIP.py (Auto-start)
```bash
@reboot sleep 30 && source ~/.raspi_env && python3 ~/RaspberryPI_Auto/Internet_Base/RaspIP.py >> ~/raspip.log 2>&1 &
```

### sync.sh (Nightly at 11:50 PM)
```bash
50 23 * * * bash ~/RaspberryPI_Auto/sync.sh >> ~/sync.log 2>&1
```

---

## Gmail Setup

1. Go to: https://myaccount.google.com/security
2. Enable "2-Step Verification"
3. Go to: https://myaccount.google.com/apppasswords
4. Select "Mail" and "Windows Computer"
5. Copy the 16-char password

---

## Check Configuration

```bash
# View config (hide password line)
grep -v "SMTP_PASSWORD" ~/.raspi_config

# Test RaspIP.py startup — shows all loaded values (Ctrl+C to stop)
python3 ~/RaspberryPI_Auto/Internet_Base/RaspIP.py

# Test sync.sh manually
bash ~/RaspberryPI_Auto/Internet_Base/sync.sh
```

---

## Permissions

```bash
# Correct permissions
chmod 600 ~/.raspi_env      # User read/write only
chmod 600 ~/.msmtprc        # User read/write only
chmod 755 ~/.raspi_state.json # Readable by all, writable by owner
chmod 755 setup_config.sh   # Executable
chmod 755 sync.sh           # Executable
chmod 755 Internet_Base/RaspIP.py # Executable
```

---

## Documentation

- **README.md** — Main documentation
- **FILES_CONFIGURATION.md** — Configuration details
- **setup_config.sh** — Interactive setup
- **VERIFICATION_CHECKLIST.md** — After setup check
- **CONFIGURATION_COMPARISON.md** — Tool differences
- **SETUP_COMPLETE.md** — How everything works
- **Internet_Base/SETUP_RASPIP.md** — RaspIP details

---

## ~/.raspi_config Reference

```bash
# ── Required ───────────────────────────────────────────
SENDER_EMAIL="your_gmail@gmail.com"
SMTP_PASSWORD="your16charapppassword"
RECIPIENT_EMAIL="recipient@gmail.com"

# ── Repository (sync.sh) ───────────────────────────────
REPO="/home/pi/RaspberryPI_Auto"
BRANCH="main"

# ── Notification (both tools) ──────────────────────────
DEVICE_NAME="MyRaspberryPi"
EMAIL_SUBJECT="Raspberry Pi IP address update"

# ── Advanced (RaspIP.py) ───────────────────────────────
CHECK_INTERVAL_SECONDS="3600"
STATE_FILE="/home/pi/.raspi_state.json"
```

---

## .msmtprc Reference

```
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account        gmail
host           smtp.gmail.com
port           587
from           your_email@gmail.com
user           your_email@gmail.com
password       xxxx xxxx xxxx xxxx

account default : gmail
```

---

## Security Checklist

- [ ] Never commit ~/.raspi_env
- [ ] Never commit ~/.msmtprc
- [ ] Set permissions to 600
- [ ] Use Gmail App Password (not regular password)
- [ ] Enable 2FA on Gmail
- [ ] Keep .gitignore updated
- [ ] Don't share config files

---

## Shortcuts

```bash
# View everything about RaspIP
source ~/.raspi_env && env | grep RASPI_IP_

# Reload config
source ~/.raspi_env

# Edit config
nano ~/.raspi_env      # For RaspIP.py
nano ~/.msmtprc        # For sync.sh

# View logs
tail -f ~/raspip.log   # RaspIP.py log
tail -f ~/sync.log     # sync.sh log
tail -f ~/.msmtp.log   # msmtp debug log

# Kill RaspIP.py
pkill -f RaspIP.py

# Check what's running
ps aux | grep -E "RaspIP|sync"
```

---

## Emergency: Reset Configuration

```bash
# Remove old configs
rm ~/.raspi_env ~/.msmtprc

# Regenerate from templates
cd ~/RaspberryPI_Auto
cp .raspi_env.template ~/.raspi_env
cp .msmtprc.template ~/.msmtprc

# Edit them
nano ~/.raspi_env
nano ~/.msmtprc
chmod 600 ~/.msmtprc

# Test
source ~/.raspi_env
python3 Internet_Base/RaspIP.py
```

---

**Quick question?** Check [FILES_CONFIGURATION.md](FILES_CONFIGURATION.md)
**Still stuck?** Check [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)
