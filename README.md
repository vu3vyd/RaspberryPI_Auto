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

**Configuration:** All settings live in a single shared file `~/.raspi_config` —
used by both RaspIP.py and sync.sh.

```
SENDER_EMAIL    — Gmail address used as sender        (required)
SMTP_PASSWORD   — Gmail App Password                  (required)
RECIPIENT_EMAIL — Where notifications are sent        (required)
DEVICE_NAME     — Name shown in email subjects/bodies (default: hostname)
EMAIL_SUBJECT   — Subject line for IP-change emails   (default: "Raspberry Pi IP address update")
CHECK_INTERVAL_SECONDS — How often to check, seconds  (default: 3600)
STATE_FILE      — Where last-known IPs are stored     (default: raspip_last_ips.json)
```

**Quick Start:**
```bash
cp raspi_config.template ~/.raspi_config
nano ~/.raspi_config      # fill in your Gmail credentials and recipient
chmod 600 ~/.raspi_config

python3 Internet_Base/RaspIP.py
```

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

**Configuration:** Reads from `~/.raspi_config` (same file as RaspIP.py).
Set `REPO`, `BRANCH`, `SENDER_EMAIL`, `SMTP_PASSWORD`, `RECIPIENT_EMAIL`, and `DEVICE_NAME` there — no hardcoded values to edit in the script.

**Installation & Setup:**
```bash
# Install msmtp (used by sync.sh for email sending)
sudo apt-get install msmtp msmtp-mta

# Create shared config (if not already done)
cp raspi_config.template ~/.raspi_config
nano ~/.raspi_config
chmod 600 ~/.raspi_config

# Create cron job (runs daily at 11:50 PM)
(crontab -l 2>/dev/null; echo "50 23 * * * /home/pi/RaspberryPI_Auto/Internet_Base/sync.sh") | crontab -

chmod +x Internet_Base/sync.sh
```

**Log File:**
Check `sync.log` in the repository for historical sync information.

---

## Quick Start

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/vu3vyd/RaspberryPI_Auto.git ~/RaspberryPI_Auto
cd ~/RaspberryPI_Auto

# 2. Create the shared config file (one file for everything)
cp raspi_config.template ~/.raspi_config
nano ~/.raspi_config      # fill in sender, password, recipient, device name
chmod 600 ~/.raspi_config

# 3. Install dependencies
pip install pyserial pynmea2           # for GPS
sudo apt-get install msmtp msmtp-mta   # for sync.sh email

# 4. Make scripts executable
chmod +x Internet_Base/sync.sh Internet_Base/RaspIP.py Hardware_Base/GPSTest.py

# 5. Run
python3 Internet_Base/RaspIP.py        # IP monitoring
bash Internet_Base/sync.sh             # Git sync (test run)
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
