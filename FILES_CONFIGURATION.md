# Configuration Files Organization Guide

## File Structure Overview

```
RaspberryPI_Auto/
├── .msmtprc.template          ← Template for sync.sh email config
├── .raspi_env.template        ← Template for RaspIP.py env vars
├── setup_config.sh            ← Interactive setup helper script
├── Internet_Base/
│   ├── RaspIP.py              ← IP monitoring script
│   ├── SETUP_RASPIP.md        ← RaspIP detailed setup guide
│   └── GPSTest.py
├── Hardware_Base/
│   └── GPSTest.py
├── sync.sh                    ← Git sync script
├── README.md
├── CONFIGURATION_COMPARISON.md
└── IMPROVEMENTS_SUMMARY.md

~/.raspi_env                   ← YOUR personal RaspIP config (not in repo)
~/.msmtprc                     ← YOUR personal msmtp config (not in repo)
```

## Quick Start - 3 Steps

### Step 1: Clone the Repository
```bash
git clone https://github.com/vu3vyd/RaspberryPI_Auto.git ~/RaspberryPI_Auto
cd ~/RaspberryPI_Auto
```

### Step 2: Run Setup Script (EASIEST WAY)
```bash
bash setup_config.sh
```

This interactive script will:
- Ask which tools you want to configure (RaspIP.py, sync.sh, or both)
- Collect your Gmail credentials
- Create the proper configuration files
- Set secure permissions on them
- Test the configuration

### Step 3: Run Your Tools
**For RaspIP.py:**
```bash
source ~/.raspi_env
python3 ~/RaspberryPI_Auto/Internet_Base/RaspIP.py
```

**For sync.sh:**
```bash
bash ~/RaspberryPI_Auto/sync.sh
```

---

## Manual Setup (If You Prefer)

### Configure RaspIP.py Manually

1. **Copy the template:**
   ```bash
   cp .raspi_env.template ~/.raspi_env
   ```

2. **Edit the file:**
   ```bash
   nano ~/.raspi_env
   ```
   
   Replace these with your information:
   ```bash
   export RASPI_IP_SMTP_USER="your_email@gmail.com"
   export RASPI_IP_SMTP_PASSWORD="xxxx xxxx xxxx xxxx"
   export RASPI_IP_EMAIL_FROM="your_email@gmail.com"
   export RASPI_IP_EMAIL_TO="recipient@gmail.com"
   export RASPI_IP_DEVICE_NAME="MyPiDevice"
   ```

3. **Secure the file:**
   ```bash
   chmod 600 ~/.raspi_env
   ```

4. **Test it:**
   ```bash
   source ~/.raspi_env
   python3 ~/RaspberryPI_Auto/Internet_Base/RaspIP.py
   ```

### Configure sync.sh Manually

1. **Copy the template:**
   ```bash
   cp .msmtprc.template ~/.msmtprc
   ```

2. **Edit the file:**
   ```bash
   nano ~/.msmtprc
   ```
   
   Replace these with your information:
   ```
   from           your_email@gmail.com
   user           your_email@gmail.com
   password       xxxx xxxx xxxx xxxx
   ```

3. **Secure the file:**
   ```bash
   chmod 600 ~/.msmtprc
   ```

4. **Edit sync.sh:**
   ```bash
   nano sync.sh
   ```
   
   Change these variables:
   ```bash
   TO="your_email@gmail.com"
   FROM="your_gmail@gmail.com"
   ```

5. **Test it:**
   ```bash
   bash sync.sh
   ```

---

## File Locations Explained

### Repository Files (in git)
These are committed to the repository:
- `setup_config.sh` — Interactive setup helper
- `.msmtprc.template` — Template for msmtp config
- `.raspi_env.template` — Template for RaspIP env vars

### Personal Configuration Files (NOT in git)
These stay on your system, not in the repository:
- `~/.raspi_env` — Your RaspIP credentials and settings
- `~/.msmtprc` — Your msmtp Gmail configuration

**⚠️ IMPORTANT:** Never commit `~/.raspi_env` or `~/.msmtprc` to git. They contain your password!

Add to `.gitignore` if needed:
```bash
echo "~/.raspi_env" >> .gitignore
echo "~/.msmtprc" >> .gitignore
```

---

## Configuration Comparison

| Aspect | RaspIP.py | sync.sh |
|--------|-----------|---------|
| **Config Method** | Environment variables | ~/.msmtprc file |
| **Config File** | ~/.raspi_env | ~/.msmtprc |
| **Email System** | Gmail SMTP (smtplib) | msmtp command |
| **Where to Set** | Before running Python | System-wide for mail command |
| **Setup Script** | ✓ Included | ✓ Included |
| **Template** | .raspi_env.template | .msmtprc.template |

---

## Gmail Prerequisites

### For Both RaspIP.py and sync.sh

1. **Enable 2-Factor Authentication:**
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate Gmail App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows (or Linux) Computer"
   - Google generates a 16-character password
   - Copy and paste it into your configuration

⚠️ **Important:** 
- Use the **App Password**, NOT your regular Gmail password
- Regular Gmail password will NOT work with SMTP
- App password looks like: `xxxx xxxx xxxx xxxx`

---

## Troubleshooting

### "Can't find configuration file"

**For RaspIP.py:**
```bash
# Check if ~/.raspi_env exists
ls -la ~/.raspi_env

# If missing, create it
cp ~/RaspberryPI_Auto/.raspi_env.template ~/.raspi_env
nano ~/.raspi_env
chmod 600 ~/.raspi_env
```

**For sync.sh:**
```bash
# Check if ~/.msmtprc exists
ls -la ~/.msmtprc

# If missing, create it
cp ~/RaspberryPI_Auto/.msmtprc.template ~/.msmtprc
nano ~/.msmtprc
chmod 600 ~/.msmtprc
```

### "Permission denied on .msmtprc"

msmtp requires strict file permissions:
```bash
chmod 600 ~/.msmtprc
ls -la ~/.msmtprc  # Should show: -rw------- 
```

### "SMTP Authentication failed"

1. Verify you're using **Gmail App Password**, not regular password
2. Check for trailing spaces in password
3. Ensure 2-Factor Authentication is enabled
4. Regenerate the app password

### "Email configuration incomplete"

RaspIP.py validates that all required environment variables are set:
```bash
# Check what's set
env | grep RASPI_IP

# Should show:
# RASPI_IP_SMTP_USER=...
# RASPI_IP_SMTP_PASSWORD=...
# RASPI_IP_EMAIL_FROM=...
# RASPI_IP_EMAIL_TO=...
```

---

## Best Practices

✅ **DO:**
- Keep configuration files outside the repository
- Use strong permissions (600) on config files
- Use Gmail App Passwords (not regular password)
- Enable 2-Factor Authentication on Gmail
- Test configuration before running in production
- Run setup_config.sh for automatic setup

❌ **DON'T:**
- Commit ~/.raspi_env to git
- Commit ~/.msmtprc to git
- Use regular Gmail password with SMTP
- Share your configuration files
- Leave config files with open permissions (777)
- Disable 2-Factor Authentication on Gmail account

---

## Running with Cron

### RaspIP.py Auto-start

```bash
# Edit crontab
crontab -e

# Add this line to start at boot
@reboot sleep 30 && source ~/.raspi_env && python3 ~/RaspberryPI_Auto/Internet_Base/RaspIP.py >> ~/raspip.log 2>&1 &
```

### sync.sh Auto-sync (Nightly)

```bash
# Edit crontab
crontab -e

# Add this line to run at 11:50 PM daily
50 23 * * * ~/RaspberryPI_Auto/sync.sh >> ~/sync.log 2>&1
```

---

## Getting Help

If things aren't working:

1. **Check RaspIP.py logs:**
   ```bash
   # Run manually to see errors
   source ~/.raspi_env
   python3 ~/RaspberryPI_Auto/Internet_Base/RaspIP.py
   ```

2. **Check sync.sh logs:**
   ```bash
   # Check the log file
   cat ~/RaspberryPI_Auto/sync.log
   
   # Or check msmtp log
   tail -f ~/.msmtp.log
   ```

3. **Test Gmail SMTP:**
   ```bash
   # For RaspIP.py
   python3 << 'EOF'
   import smtplib
   from email.message import EmailMessage
   msg = EmailMessage()
   msg.set_content("Test")
   msg["Subject"] = "Test"
   msg["From"] = "your_email@gmail.com"
   msg["To"] = "recipient@gmail.com"
   try:
       with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
           smtp.starttls()
           smtp.login("your_email@gmail.com", "xxxx xxxx xxxx xxxx")
           smtp.send_message(msg)
       print("Success!")
   except Exception as e:
       print(f"Error: {e}")
   EOF
   ```

4. **Test msmtp:**
   ```bash
   echo "Test message" | msmtp -v recipient@gmail.com
   ```

5. **Read detailed setup guides:**
   - [SETUP_RASPIP.md](Internet_Base/SETUP_RASPIP.md)
   - [CONFIGURATION_COMPARISON.md](CONFIGURATION_COMPARISON.md)

---

## Summary

| Tool | Config File | Template | Setup Helper |
|------|-------------|----------|--------------|
| RaspIP.py | ~/.raspi_env | .raspi_env.template | setup_config.sh |
| sync.sh | ~/.msmtprc | .msmtprc.template | setup_config.sh |

**Easiest way to get started:**
```bash
bash ~/RaspberryPI_Auto/setup_config.sh
```

All three configuration files exist in the repo:
1. ✅ **setup_config.sh** — Interactive setup (creates the rest)
2. ✅ **.raspi_env.template** — Template for RaspIP.py
3. ✅ **.msmtprc.template** — Template for sync.sh

No more missing file errors! 🎉
