# RaspberryPI_Auto

A collection of automation scripts and utilities for Raspberry Pi systems. These projects focus on monitoring, synchronization, and hardware integration.

## Projects Overview

### 1. Internet_Base/ — IP Address Monitoring
**File:** `Internet_Base/RaspIP.py`

Monitor Raspberry Pi IP addresses and receive email notifications when they change. Useful for tracking dynamic IP changes or ensuring connectivity.

**Features:**
- Monitors both IPv4 and IPv6 addresses
- Detects changes across all network interfaces (excluding loopback)
- Sends email notifications on IP changes
- Supports custom device naming for email reports
- Configurable check intervals
- Comprehensive logging and error handling
- Pre-startup configuration validation

**Setup Guide:** See [Internet_Base/SETUP_RASPIP.md](Internet_Base/SETUP_RASPIP.md) for detailed setup instructions

**Configuration:**

SMTP credentials (`host`, `user`, `password`, `from`) are read from `~/.msmtprc` —
the same file used by sync.sh. Only the recipient address is set via env var.

```bash
# REQUIRED — recipient address
RASPI_IP_EMAIL_TO                # Where to send notifications

# OPTIONAL — customisation
RASPI_IP_DEVICE_NAME             # Device name in emails (default: system hostname)
RASPI_IP_EMAIL_SUBJECT           # Email subject template (default: "Raspberry Pi IP address update")
RASPI_IP_CHECK_INTERVAL_SECONDS  # Check interval in seconds (default: 3600)
RASPI_IP_STATE_FILE              # State file path (default: raspip_last_ips.json)
```

**Quick Start:**
```bash
# 1. Create ~/.msmtprc (if not already done for sync.sh)
cp .msmtprc.template ~/.msmtprc
nano ~/.msmtprc      # fill in your Gmail address and App Password
chmod 600 ~/.msmtprc

# 2. Set recipient and run
export RASPI_IP_EMAIL_TO="recipient@gmail.com"
python3 Internet_Base/RaspIP.py
```

**Note:** Both RaspIP.py and sync.sh share `~/.msmtprc` for SMTP credentials. See [Internet_Base/CONFIGURATION_COMPARISON.md](Internet_Base/CONFIGURATION_COMPARISON.md) for details.

---

### 2. Hardware_Base/ — GPS Testing Utility
**File:** `Hardware_Base/GPSTest.py`

Test and monitor GPS data from a connected GPS module. Parses NMEA sentences to extract timestamp, latitude, and longitude information.

**Features:**
- Reads NMEA data from serial port (`/dev/serial0`)
- Parses GPRMC and GPGGA sentences
- Displays timestamp, latitude, and longitude
- Handles serial errors gracefully

**Requirements:**
- GPS module connected to Pi's serial port
- `pyserial` library
- `pynmea2` library

**Installation:**
```bash
pip install pyserial pynmea2
```

**Usage:**
```bash
python3 Hardware_Base/GPSTest.py
```

Output example:
```
Waiting for GPS Lock...
Timestamp: 14:30:45 | Lat: 37.7749 | Lon: -122.4194
```

---

### 3. sync.sh — Automated GitHub Synchronization
**File:** `sync.sh`

Automated nightly Git repository sync with email status notifications. Perfect for keeping your Pi updated with the latest code changes.

**Features:**
- Runs nightly via cron (11:50 PM by default)
- Fetches remote first; only pulls and emails if new commits exist (silent on no change)
- Logs all sync activities to `sync.log`
- Sends email notifications with device hostname on successful pull or fetch failure
- Reports success or failure with detailed git output

**Configuration (inside `sync.sh`):**
```bash
REPO="/home/pi/RaspberryPI_Auto"          # Repository path
BRANCH="main"                              # Branch to sync
LOG="/home/pi/RaspberryPI_Auto/sync.log"  # Log file location
TO="your_email@gmail.com"                  # Email recipient
FROM="your_gmail@gmail.com"                # Gmail sender
```

**Email Setup:**
Requires `msmtp` with Gmail configuration in `~/.msmtprc`:
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
password       your_app_password

account default : gmail
```

**Installation & Setup:**
```bash
# Install msmtp
sudo apt-get install msmtp msmtp-mta

# Create cron job (runs daily at 11:50 PM)
(crontab -l 2>/dev/null; echo "50 23 * * * /home/pi/RaspberryPI_Auto/sync.sh") | crontab -

# Make sync.sh executable
chmod +x sync.sh
```

**Log File:**
Check `sync.log` in the repository for historical sync information.

---

## Quick Start

### Easiest Way - Use Setup Script

```bash
# 1. Clone the repository
git clone https://github.com/vu3vyd/RaspberryPI_Auto.git ~/RaspberryPI_Auto
cd ~/RaspberryPI_Auto

# 2. Run the interactive setup (handles all configuration)
bash setup_config.sh

# 3. Run your tools
source ~/.raspi_env
python3 Internet_Base/RaspIP.py    # For IP monitoring
# OR
bash sync.sh                        # For Git sync
```

### Manual Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vu3vyd/RaspberryPI_Auto.git ~/RaspberryPI_Auto
   cd ~/RaspberryPI_Auto
   ```

2. **Install dependencies:**
   ```bash
   pip install pyserial pynmea2
   sudo apt-get install msmtp msmtp-mta
   ```

3. **Choose which tools you need and configure:**
   - **For RaspIP.py:** Copy `.raspi_env.template` to `~/.raspi_env` and edit it
   - **For sync.sh:** Copy `.msmtprc.template` to `~/.msmtprc` and edit it
   - See [FILES_CONFIGURATION.md](FILES_CONFIGURATION.md) for detailed instructions

4. **Make scripts executable:**
   ```bash
   chmod +x setup_config.sh sync.sh Internet_Base/RaspIP.py Hardware_Base/GPSTest.py
   ```

## Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** — Quick command reference (bookmark this!)
- **[FILES_CONFIGURATION.md](FILES_CONFIGURATION.md)** — Configuration file organization and setup guide
- **[setup_config.sh](setup_config.sh)** — Interactive setup script (easiest way to configure)
- [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md) — After setup verification
- [CONFIGURATION_COMPARISON.md](CONFIGURATION_COMPARISON.md) — Explains differences between RaspIP.py and sync.sh
- [Internet_Base/SETUP_RASPIP.md](Internet_Base/SETUP_RASPIP.md) — Complete RaspIP.py setup guide with troubleshooting
- [SETUP_COMPLETE.md](SETUP_COMPLETE.md) — How the complete system works
- [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md) — Technical details of improvements made

## Requirements

- Raspberry Pi (any recent model)
- Python 3.6+
- `pyserial` (for GPS testing)
- `pynmea2` (for GPS parsing)
- `msmtp` (for email notifications in sync.sh)

## License

This project is part of the RaspberryPI_Auto collection.

## Repository
- GitHub: https://github.com/vu3vyd/RaspberryPI_Auto
