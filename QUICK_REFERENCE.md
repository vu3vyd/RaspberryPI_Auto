# Quick Reference Card

## Setup (Choose One Method)

### Method 1: Automatic ⭐ (Easiest)
```bash
bash setup_config.sh
```
Answer prompts → Done!

### Method 2: Templates
```bash
cp .raspi_env.template ~/.raspi_env
nano ~/.raspi_env
# Then copy and edit for sync.sh
cp .msmtprc.template ~/.msmtprc
nano ~/.msmtprc
chmod 600 ~/.msmtprc
```

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
| RaspIP config | ~/.raspi_env | RASPI_IP_* env vars |
| sync.sh config | ~/.msmtprc | Gmail SMTP settings |
| State file | ~/.raspi_state.json | Last known IPs |
| Sync log | ~/RaspberryPI_Auto/sync.log | Sync history |

---

## Common Troubleshooting

| Problem | Solution |
|---------|----------|
| File not found | Run: `bash setup_config.sh` |
| Permission denied | Run: `chmod 600 ~/.msmtprc` |
| Auth failed | Check Gmail App Password |
| No email sent | Check RASPI_IP_* variables |
| Can't find template | Templates in repo root |

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
# View RaspIP config (hide password)
grep -v PASSWORD ~/.raspi_env

# View sync config (hide password)
grep -v "^password" ~/.msmtprc

# Test email (RaspIP)
source ~/.raspi_env
python3 -c "
import smtplib
from email.message import EmailMessage
msg = EmailMessage()
msg.set_content('Test')
msg['Subject'] = 'Test'
msg['From'] = '$RASPI_IP_EMAIL_FROM'
msg['To'] = '$RASPI_IP_EMAIL_TO'
try:
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('$RASPI_IP_SMTP_USER', '$RASPI_IP_SMTP_PASSWORD')
        smtp.send_message(msg)
    print('Success!')
except Exception as e:
    print(f'Error: {e}')
"

# Test email (sync.sh)
echo "Test" | msmtp -v your_email@gmail.com
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

## Environment Variables Reference

```bash
# REQUIRED for RaspIP.py
RASPI_IP_SMTP_USER          # Gmail address
RASPI_IP_SMTP_PASSWORD      # Gmail App Password
RASPI_IP_EMAIL_FROM         # Sender address
RASPI_IP_EMAIL_TO           # Recipient address

# OPTIONAL for RaspIP.py
RASPI_IP_DEVICE_NAME        # Device name (default: hostname)
RASPI_IP_CHECK_INTERVAL_SECONDS    # Check frequency (default: 3600)
RASPI_IP_STATE_FILE         # State file path
RASPI_IP_SMTP_SERVER        # SMTP server (default: smtp.gmail.com)
RASPI_IP_SMTP_PORT          # SMTP port (default: 587)
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
