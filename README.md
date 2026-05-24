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

**Environment Variables:**
```bash
RASPI_IP_STATE_FILE              # Path to state file (default: raspip_last_ips.json)
RASPI_IP_SMTP_SERVER             # SMTP server (default: smtp.gmail.com)
RASPI_IP_SMTP_PORT               # SMTP port (default: 587)
RASPI_IP_SMTP_USER               # SMTP username
RASPI_IP_SMTP_PASSWORD           # SMTP password
RASPI_IP_EMAIL_FROM              # Sender email address
RASPI_IP_EMAIL_TO                # Recipient email address
RASPI_IP_EMAIL_SUBJECT           # Email subject (default: "Raspberry Pi IP address update")
RASPI_IP_DEVICE_NAME             # Custom device name for email reports (default: system hostname)
RASPI_IP_CHECK_INTERVAL_SECONDS   # Check interval in seconds (default: 3600 / 1 hour)
```

**Usage:**
```bash
# Set device name for email notifications
export RASPI_IP_DEVICE_NAME="MyPiDevice"
export RASPI_IP_SMTP_USER="your_email@gmail.com"
export RASPI_IP_SMTP_PASSWORD="your_app_password"
export RASPI_IP_EMAIL_FROM="your_email@gmail.com"
export RASPI_IP_EMAIL_TO="recipient@gmail.com"

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
- Pulls latest changes from GitHub
- Logs all sync activities
- Sends email notifications with device hostname
- Reports success or failure with detailed information

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

3. **Configure environment variables and email settings** as needed for each utility.

4. **Make scripts executable:**
   ```bash
   chmod +x sync.sh Internet_Base/RaspIP.py Hardware_Base/GPSTest.py
   ```

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
