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
  - Select "Mail" and "Windows (or Linux) Computer"
  - Copy the generated 16-character password

### 3. Network Requirements
- [ ] Device has internet connectivity
- [ ] Can reach smtp.gmail.com:587 (Gmail SMTP server)
- [ ] Port 587 is not blocked by firewall

## Configuration

### Set Required Environment Variables

Before running the script, set these environment variables:

```bash
# REQUIRED - Email configuration
export RASPI_IP_SMTP_USER="your_email@gmail.com"              # Your Gmail address
export RASPI_IP_SMTP_PASSWORD="xxxx xxxx xxxx xxxx"           # 16-char Gmail app password
export RASPI_IP_EMAIL_FROM="your_email@gmail.com"            # Sender (same as SMTP_USER)
export RASPI_IP_EMAIL_TO="recipient@gmail.com"               # Where to send notifications

# OPTIONAL - Customization
export RASPI_IP_DEVICE_NAME="MyPiDevice"                     # Device name (default: hostname)
export RASPI_IP_CHECK_INTERVAL_SECONDS="3600"                # Check interval in seconds (default: 1 hour)
export RASPI_IP_STATE_FILE="/home/pi/raspip_state.json"      # State file location (default: ./raspip_last_ips.json)
```

### Create a Configuration Script

For convenience, create `~/.raspi_ip_config.sh`:

```bash
#!/bin/bash
export RASPI_IP_SMTP_USER="your_email@gmail.com"
export RASPI_IP_SMTP_PASSWORD="xxxx xxxx xxxx xxxx"
export RASPI_IP_EMAIL_FROM="your_email@gmail.com"
export RASPI_IP_EMAIL_TO="recipient@gmail.com"
export RASPI_IP_DEVICE_NAME="MyPiDevice"
export RASPI_IP_CHECK_INTERVAL_SECONDS="3600"
export RASPI_IP_STATE_FILE="/home/pi/raspip_state.json"
```

Then load it before running:
```bash
source ~/.raspi_ip_config.sh
python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py
```

## Running the Script

### Test Run (with output)
```bash
source ~/.raspi_ip_config.sh
python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py
```

You should see log messages like:
```
[2026-05-24 14:30:45] INFO: Configuration validated successfully
[2026-05-24 14:30:45] INFO: Device Name: MyPiDevice
[2026-05-24 14:30:45] INFO: State File: /home/pi/raspip_state.json
[2026-05-24 14:30:45] INFO: Check Interval: 3600 seconds (60 minutes)
[2026-05-24 14:30:45] INFO: Starting RaspIP monitor for device: MyPiDevice
```

### Run in Background (with systemd)

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
EnvironmentFile=/home/pi/.raspi_ip_config.sh
ExecStart=/usr/bin/python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Then enable and start:
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

Add to crontab with auto-restart on failure:

```bash
# Edit crontab
crontab -e

# Add this line (runs at boot and restarts if stopped)
@reboot source /home/pi/.raspi_ip_config.sh && python3 /home/pi/RaspberryPI_Auto/Internet_Base/RaspIP.py >> /home/pi/raspip.log 2>&1 &
```

## Troubleshooting

### ❌ "Configuration validation failed"

**Check these things:**

1. **Missing EMAIL_TO**
   ```bash
   echo $RASPI_IP_EMAIL_TO
   # Should show an email address, not empty
   ```

2. **Missing SMTP_USER**
   ```bash
   echo $RASPI_IP_SMTP_USER
   # Should show your Gmail address
   ```

3. **Missing SMTP_PASSWORD**
   ```bash
   echo $RASPI_IP_SMTP_PASSWORD
   # Should show 16 characters with spaces (xxxx xxxx xxxx xxxx)
   # ⚠️ NOT your regular Gmail password!
   ```

4. **State file directory not writable**
   ```bash
   mkdir -p $(dirname $RASPI_IP_STATE_FILE)
   chmod 755 $(dirname $RASPI_IP_STATE_FILE)
   ```

### ❌ "SMTP authentication failed"

**Solutions:**

1. Verify Gmail App Password (not regular password)
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or Linux)
   - Create a new one if needed

2. Ensure 2-factor authentication is enabled on Gmail account
   - https://myaccount.google.com/security

3. Check for extra spaces in password:
   ```bash
   # This is WRONG (extra space at end):
   export RASPI_IP_SMTP_PASSWORD="xxxx xxxx xxxx xxxx "
   
   # This is CORRECT:
   export RASPI_IP_SMTP_PASSWORD="xxxx xxxx xxxx xxxx"
   ```

### ❌ "Network error while connecting"

**Causes and solutions:**

1. **No internet connection**
   ```bash
   ping 8.8.8.8
   ```

2. **Port 587 blocked**
   ```bash
   telnet smtp.gmail.com 587
   # If it hangs or connection refused, port is blocked
   ```

3. **Firewall blocking outbound SMTP**
   - Contact your network administrator
   - Or use a VPN

### ✅ "Email sent successfully"

Great! The monitor is working. It will:
- Check for IP changes every 3600 seconds (1 hour by default)
- Send an email only when an IP address change is detected
- Log all activities to stdout

### ❓ "No email received after IP change"

1. Check your spam/junk folder (add to contacts if needed)

2. Verify the email was actually sent:
   ```bash
   # Look for "Email sent successfully" in logs
   ```

3. Check if IP actually changed (the script only sends on changes):
   ```bash
   # View current state
   cat $(RASPI_IP_STATE_FILE}
   ```

## Important Notes

⚠️ **Security:**
- Never commit `.raspi_ip_config.sh` to version control
- Never share your Gmail App Password
- Consider restricting permissions: `chmod 600 ~/.raspi_ip_config.sh`

⚠️ **Differences from sync.sh:**
- **RaspIP.py** uses Gmail SMTP directly (smtplib)
- **sync.sh** uses msmtp command with ~/.msmtprc file
- They are **independent** systems with different configurations
- No shared setup between them

✅ **Logging:**
- All activities are logged with timestamps
- Errors are clearly reported
- Check logs when troubleshooting

## Support

If you encounter issues:
1. Check the logs (they show exactly what's happening)
2. Verify all environment variables are set correctly
3. Test Gmail connectivity separately: `telnet smtp.gmail.com 587`
4. Ensure your Gmail App Password is correct and 2FA is enabled
